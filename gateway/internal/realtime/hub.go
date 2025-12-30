package realtime

import (
	"context"
	"encoding/json"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
	"go.uber.org/zap"
)

// Hub maintains active WebSocket connections
type Hub struct {
	clients    map[string]*Client
	register   chan *Client
	unregister chan *Client
	broadcast  chan *Message
	mu         sync.RWMutex
	logger     *zap.Logger
}

// Client represents a WebSocket connection
type Client struct {
	ID       string
	UserID   string
	Hub      *Hub
	Conn     *websocket.Conn
	Send     chan []byte
	mu       sync.Mutex
}

// Message represents a WebSocket message
type Message struct {
	Type      string                 `json:"type"`
	UserID    string                 `json:"user_id,omitempty"`
	Data      map[string]interface{} `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
}

// NewHub creates a new WebSocket hub
func NewHub(logger *zap.Logger) *Hub {
	return &Hub{
		clients:    make(map[string]*Client),
		register:   make(chan *Client),
		unregister: make(chan *Client),
		broadcast:  make(chan *Message, 256),
		logger:     logger,
	}
}

// Run starts the hub
func (h *Hub) Run(ctx context.Context) {
	h.logger.Info("Starting WebSocket hub")

	for {
		select {
		case client := <-h.register:
			h.mu.Lock()
			h.clients[client.ID] = client
			h.mu.Unlock()
			h.logger.Info("Client registered",
				zap.String("client_id", client.ID),
				zap.String("user_id", client.UserID),
			)

		case client := <-h.unregister:
			h.mu.Lock()
			if _, ok := h.clients[client.ID]; ok {
				delete(h.clients, client.ID)
				close(client.Send)
				h.logger.Info("Client unregistered", zap.String("client_id", client.ID))
			}
			h.mu.Unlock()

		case message := <-h.broadcast:
			h.mu.RLock()
			for _, client := range h.clients {
				// If message has a specific user, only send to that user
				if message.UserID != "" && client.UserID != message.UserID {
					continue
				}

				select {
				case client.Send <- h.marshalMessage(message):
				default:
					// Client's send channel is full, close the connection
					h.mu.RUnlock()
					h.unregister <- client
					h.mu.RLock()
				}
			}
			h.mu.RUnlock()

		case <-ctx.Done():
			h.logger.Info("Stopping WebSocket hub")
			return
		}
	}
}

// RegisterClient registers a new client
func (h *Hub) RegisterClient(userID string, conn *websocket.Conn) *Client {
	client := &Client{
		ID:     uuid.New().String(),
		UserID: userID,
		Hub:    h,
		Conn:   conn,
		Send:   make(chan []byte, 256),
	}

	h.register <- client
	return client
}

// UnregisterClient unregisters a client
func (h *Hub) UnregisterClient(client *Client) {
	h.unregister <- client
}

// Broadcast sends a message to all connected clients
func (h *Hub) Broadcast(msgType string, data map[string]interface{}) {
	h.broadcast <- &Message{
		Type:      msgType,
		Data:      data,
		Timestamp: time.Now(),
	}
}

// BroadcastToUser sends a message to a specific user
func (h *Hub) BroadcastToUser(userID, msgType string, data map[string]interface{}) {
	h.broadcast <- &Message{
		Type:      msgType,
		UserID:    userID,
		Data:      data,
		Timestamp: time.Now(),
	}
}

// GetClientCount returns the number of connected clients
func (h *Hub) GetClientCount() int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.clients)
}

// GetUserClientCount returns the number of connections for a specific user
func (h *Hub) GetUserClientCount(userID string) int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	
	count := 0
	for _, client := range h.clients {
		if client.UserID == userID {
			count++
		}
	}
	return count
}

func (h *Hub) marshalMessage(msg *Message) []byte {
	data, err := json.Marshal(msg)
	if err != nil {
		h.logger.Error("Failed to marshal message", zap.Error(err))
		return []byte("{}")
	}
	return data
}

// ReadPump pumps messages from the WebSocket connection to the hub
func (c *Client) ReadPump() {
	defer func() {
		c.Hub.UnregisterClient(c)
		c.Conn.Close()
	}()

	c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.Conn.SetPongHandler(func(string) error {
		c.Conn.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := c.Conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				c.Hub.logger.Error("WebSocket error", zap.Error(err))
			}
			break
		}

		// Handle incoming messages (e.g., subscriptions, commands)
		var msg Message
		if err := json.Unmarshal(message, &msg); err != nil {
			c.Hub.logger.Error("Failed to unmarshal message", zap.Error(err))
			continue
		}

		// Process message based on type
		c.handleMessage(&msg)
	}
}

// WritePump pumps messages from the hub to the WebSocket connection
func (c *Client) WritePump() {
	ticker := time.NewTicker(54 * time.Second)
	defer func() {
		ticker.Stop()
		c.Conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.Send:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				// Hub closed the channel
				c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.Conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			// Add queued messages to current websocket message
			n := len(c.Send)
			for i := 0; i < n; i++ {
				w.Write([]byte{'\n'})
				w.Write(<-c.Send)
			}

			if err := w.Close(); err != nil {
				return
			}

		case <-ticker.C:
			c.Conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

func (c *Client) handleMessage(msg *Message) {
	c.Hub.logger.Debug("Received message",
		zap.String("type", msg.Type),
		zap.String("client_id", c.ID),
	)

	// Handle different message types
	switch msg.Type {
	case "ping":
		// Respond with pong
		c.Send <- c.Hub.marshalMessage(&Message{
			Type:      "pong",
			Data:      map[string]interface{}{},
			Timestamp: time.Now(),
		})

	case "subscribe":
		// Handle subscription to specific events
		// TODO: Implement subscription logic

	case "unsubscribe":
		// Handle unsubscription
		// TODO: Implement unsubscription logic

	default:
		c.Hub.logger.Warn("Unknown message type", zap.String("type", msg.Type))
	}
}
