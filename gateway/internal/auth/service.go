package auth

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/redis/go-redis/v9"
	"go.uber.org/zap"
	"golang.org/x/crypto/bcrypt"
)

type AuthService struct {
	db            *sqlx.DB
	redis         *redis.Client
	jwtSecret     string
	centralURL    string
	pulseInterval time.Duration
	logger        *zap.Logger
}

func NewAuthService(db *sqlx.DB, redisClient *redis.Client, jwtSecret, centralURL string, pulseInterval time.Duration, logger *zap.Logger) *AuthService {
	return &AuthService{
		db:            db,
		redis:         redisClient,
		jwtSecret:     jwtSecret,
		centralURL:    centralURL,
		pulseInterval: pulseInterval,
		logger:        logger,
	}
}

// JWT Claims structure
type Claims struct {
	UserID   string   `json:"user_id"`
	Email    string   `json:"email"`
	Role     string   `json:"role"`
	Features []string `json:"features"`
	OrgID    string   `json:"org_id"`
	jwt.RegisteredClaims
}

// User model
type User struct {
	ID               string         `db:"id"`
	Email            string         `db:"email"`
	Username         string         `db:"username"`
	PasswordHash     string         `db:"password_hash"`
	FullName         sql.NullString `db:"full_name"`
	OrganizationID   sql.NullString `db:"organization_id"`
	Role             string         `db:"role"`
	Features         []byte         `db:"features"`
	IsActive         bool           `db:"is_active"`
	TermsAcceptedAt  sql.NullTime   `db:"terms_accepted_at"`
	TermsVersion     sql.NullString `db:"terms_version"`
	CreatedAt        time.Time      `db:"created_at"`
	UpdatedAt        time.Time      `db:"updated_at"`
	LastLoginAt      sql.NullTime   `db:"last_login_at"`
}

// Session model
type Session struct {
	ID             string    `db:"id"`
	UserID         string    `db:"user_id"`
	TokenHash      string    `db:"token_hash"`
	IPAddress      string    `db:"ip_address"`
	UserAgent      string    `db:"user_agent"`
	ExpiresAt      time.Time `db:"expires_at"`
	RevokedAt      sql.NullTime `db:"revoked_at"`
	CreatedAt      time.Time `db:"created_at"`
	LastActivityAt time.Time `db:"last_activity_at"`
}

// RegisterRequest payload
type RegisterRequest struct {
	Email          string `json:"email" binding:"required,email"`
	Username       string `json:"username" binding:"required,min=3"`
	Password       string `json:"password" binding:"required,min=8"`
	FullName       string `json:"full_name"`
	OrganizationID string `json:"organization_id"`
}

// LoginRequest payload
type LoginRequest struct {
	Email    string `json:"email" binding:"required,email"`
	Password string `json:"password" binding:"required"`
}

// LoginResponse payload
type LoginResponse struct {
	AccessToken  string   `json:"access_token"`
	RefreshToken string   `json:"refresh_token"`
	ExpiresIn    int      `json:"expires_in"`
	User         UserInfo `json:"user"`
}

type UserInfo struct {
	ID             string   `json:"id"`
	Email          string   `json:"email"`
	Username       string   `json:"username"`
	Role           string   `json:"role"`
	Features       []string `json:"features"`
	OrganizationID string   `json:"organization_id"`
}

// Register a new user
func (s *AuthService) Register(ctx context.Context, req RegisterRequest) (*User, error) {
	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("failed to hash password: %w", err)
	}

	// Create user
	user := &User{
		Email:        req.Email,
		Username:     req.Username,
		PasswordHash: string(hashedPassword),
		Role:         "analyst",
		Features:     []byte(`["port_scan", "web_scan"]`), // Basic features
		IsActive:     true,
	}

	if req.FullName != "" {
		user.FullName = sql.NullString{String: req.FullName, Valid: true}
	}

	if req.OrganizationID != "" {
		user.OrganizationID = sql.NullString{String: req.OrganizationID, Valid: true}
	}

	query := `
		INSERT INTO users (email, username, password_hash, full_name, organization_id, role, features, is_active)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		RETURNING id, created_at, updated_at
	`

	err = s.db.QueryRowContext(ctx, query,
		user.Email,
		user.Username,
		user.PasswordHash,
		user.FullName,
		user.OrganizationID,
		user.Role,
		user.Features,
		user.IsActive,
	).Scan(&user.ID, &user.CreatedAt, &user.UpdatedAt)

	if err != nil {
		return nil, fmt.Errorf("failed to create user: %w", err)
	}

	s.logger.Info("User registered", zap.String("user_id", user.ID), zap.String("email", user.Email))

	return user, nil
}

// Login authenticates a user and creates a session
func (s *AuthService) Login(ctx context.Context, req LoginRequest, ipAddress, userAgent string) (*LoginResponse, error) {
	// Get user by email
	var user User
	err := s.db.GetContext(ctx, &user, "SELECT * FROM users WHERE email = $1 AND is_active = true", req.Email)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("invalid credentials")
		}
		return nil, fmt.Errorf("database error: %w", err)
	}

	// Check if terms have been accepted
	if !user.TermsAcceptedAt.Valid {
		return nil, fmt.Errorf("terms of use must be accepted before login")
	}

	// Verify password
	err = bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(req.Password))
	if err != nil {
		return nil, fmt.Errorf("invalid credentials")
	}

	// Parse features
	var features []string
	// TODO: Properly unmarshal JSON features

	// Generate JWT token
	token, expiresIn, err := s.GenerateToken(user.ID, user.Email, user.Role, features)
	if err != nil {
		return nil, fmt.Errorf("failed to generate token: %w", err)
	}

	// Hash token for storage
	tokenHash := hashToken(token)

	// Create session
	sessionID := uuid.New().String()
	expiresAt := time.Now().Add(time.Duration(expiresIn) * time.Second)

	_, err = s.db.ExecContext(ctx, `
		INSERT INTO sessions (id, user_id, token_hash, ip_address, user_agent, expires_at)
		VALUES ($1, $2, $3, $4, $5, $6)
	`, sessionID, user.ID, tokenHash, ipAddress, userAgent, expiresAt)

	if err != nil {
		return nil, fmt.Errorf("failed to create session: %w", err)
	}

	// Update last login
	_, err = s.db.ExecContext(ctx, "UPDATE users SET last_login_at = NOW() WHERE id = $1", user.ID)
	if err != nil {
		s.logger.Error("Failed to update last login", zap.Error(err))
	}

	s.logger.Info("User logged in",
		zap.String("user_id", user.ID),
		zap.String("email", user.Email),
		zap.String("ip_address", ipAddress),
	)

	orgID := ""
	if user.OrganizationID.Valid {
		orgID = user.OrganizationID.String
	}

	return &LoginResponse{
		AccessToken:  token,
		RefreshToken: "", // TODO: Implement refresh token
		ExpiresIn:    expiresIn,
		User: UserInfo{
			ID:             user.ID,
			Email:          user.Email,
			Username:       user.Username,
			Role:           user.Role,
			Features:       features,
			OrganizationID: orgID,
		},
	}, nil
}

// GenerateToken creates a JWT token
func (s *AuthService) GenerateToken(userID, email, role string, features []string) (string, int, error) {
	expiresIn := 3600 // 1 hour

	claims := &Claims{
		UserID:   userID,
		Email:    email,
		Role:     role,
		Features: features,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Duration(expiresIn) * time.Second)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
			ID:        uuid.New().String(),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signedToken, err := token.SignedString([]byte(s.jwtSecret))
	if err != nil {
		return "", 0, err
	}

	return signedToken, expiresIn, nil
}

// ValidateToken validates a JWT token
func (s *AuthService) ValidateToken(tokenString string) (*Claims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &Claims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
		}
		return []byte(s.jwtSecret), nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(*Claims); ok && token.Valid {
		return claims, nil
	}

	return nil, jwt.ErrTokenInvalidClaims
}

// AuthMiddleware validates JWT tokens
func (s *AuthService) AuthMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		tokenString := c.GetHeader("Authorization")
		if tokenString == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "missing authorization header"})
			c.Abort()
			return
		}

		// Remove "Bearer " prefix
		if len(tokenString) > 7 && tokenString[:7] == "Bearer " {
			tokenString = tokenString[7:]
		}

		claims, err := s.ValidateToken(tokenString)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
			c.Abort()
			return
		}

		// Set user info in context
		c.Set("user_id", claims.UserID)
		c.Set("email", claims.Email)
		c.Set("role", claims.Role)
		c.Set("features", claims.Features)

		c.Next()
	}
}

// StartPulseCheck runs authorization pulse checks
func (s *AuthService) StartPulseCheck(ctx context.Context) {
	ticker := time.NewTicker(s.pulseInterval)
	defer ticker.Stop()

	s.logger.Info("Starting authorization pulse checker", zap.Duration("interval", s.pulseInterval))

	for {
		select {
		case <-ticker.C:
			s.performPulseCheck(ctx)
		case <-ctx.Done():
			s.logger.Info("Stopping authorization pulse checker")
			return
		}
	}
}

func (s *AuthService) performPulseCheck(ctx context.Context) {
	// Get all active sessions
	var sessions []Session
	err := s.db.SelectContext(ctx, &sessions, `
		SELECT * FROM sessions 
		WHERE revoked_at IS NULL AND expires_at > NOW()
	`)

	if err != nil {
		s.logger.Error("Failed to get active sessions", zap.Error(err))
		return
	}

	for _, session := range sessions {
		// TODO: Check with central authorization server
		// For now, just log the pulse check
		
		_, err = s.db.ExecContext(ctx, `
			INSERT INTO authorization_pulses (session_id, user_id, status, checked_at, next_check_at)
			VALUES ($1, $2, $3, NOW(), NOW() + INTERVAL '5 minutes')
		`, session.ID, session.UserID, "authorized")

		if err != nil {
			s.logger.Error("Failed to log pulse check", zap.Error(err))
		}
	}

	s.logger.Debug("Pulse check completed", zap.Int("sessions_checked", len(sessions)))
}

// Helper function to hash tokens
func hashToken(token string) string {
	hash := sha256.Sum256([]byte(token))
	return hex.EncodeToString(hash[:])
}
