package audit

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"go.uber.org/zap"
)

// AuditSigner handles cryptographic signing of audit logs
type AuditSigner struct {
	privateKey ed25519.PrivateKey
	publicKey  ed25519.PublicKey
	logger     *zap.Logger
}

// NewAuditSigner creates a new audit signer
// Loads keys from environment or generates new ones
func NewAuditSigner(logger *zap.Logger) (*AuditSigner, error) {
	privateKeyB64 := os.Getenv("AUDIT_SIGNING_PRIVATE_KEY")
	publicKeyB64 := os.Getenv("AUDIT_SIGNING_PUBLIC_KEY")

	var privateKey ed25519.PrivateKey
	var publicKey ed25519.PublicKey

	if privateKeyB64 != "" && publicKeyB64 != "" {
		// Load existing keys
		privBytes, err := base64.StdEncoding.DecodeString(privateKeyB64)
		if err != nil {
			return nil, fmt.Errorf("failed to decode private key: %w", err)
		}

		pubBytes, err := base64.StdEncoding.DecodeString(publicKeyB64)
		if err != nil {
			return nil, fmt.Errorf("failed to decode public key: %w", err)
		}

		privateKey = ed25519.PrivateKey(privBytes)
		publicKey = ed25519.PublicKey(pubBytes)

		logger.Info("Loaded existing audit signing keys")
	} else {
		// Generate new keys
		pub, priv, err := ed25519.GenerateKey(rand.Reader)
		if err != nil {
			return nil, fmt.Errorf("failed to generate keys: %w", err)
		}

		privateKey = priv
		publicKey = pub

		logger.Warn("Generated new audit signing keys - store these securely!",
			zap.String("public_key", base64.StdEncoding.EncodeToString(publicKey)),
		)
	}

	return &AuditSigner{
		privateKey: privateKey,
		publicKey:  publicKey,
		logger:     logger,
	}, nil
}

// SignableAuditLog represents the canonical format for signing
type SignableAuditLog struct {
	ID           int64     `json:"id"`
	UserID       string    `json:"user_id"`
	Action       string    `json:"action"`
	ResourceType string    `json:"resource_type"`
	ResourceID   string    `json:"resource_id"`
	Target       string    `json:"target"`
	Status       string    `json:"status"`
	IPAddress    string    `json:"ip_address"`
	Timestamp    time.Time `json:"timestamp"`
}

// SignLog creates a cryptographic signature for an audit log
func (s *AuditSigner) SignLog(log *SignableAuditLog) (string, error) {
	// Create canonical JSON representation (sorted keys, no whitespace)
	canonical, err := json.Marshal(log)
	if err != nil {
		return "", fmt.Errorf("failed to marshal log: %w", err)
	}

	// Sign using Ed25519
	signature := ed25519.Sign(s.privateKey, canonical)

	// Return base64-encoded signature
	return base64.StdEncoding.EncodeToString(signature), nil
}

// VerifySignature verifies a signature against a log
func (s *AuditSigner) VerifySignature(log *SignableAuditLog, signatureB64 string, publicKeyB64 string) (bool, error) {
	// Decode signature
	signature, err := base64.StdEncoding.DecodeString(signatureB64)
	if err != nil {
		return false, fmt.Errorf("failed to decode signature: %w", err)
	}

	// Decode public key
	publicKey, err := base64.StdEncoding.DecodeString(publicKeyB64)
	if err != nil {
		return false, fmt.Errorf("failed to decode public key: %w", err)
	}

	// Create canonical JSON
	canonical, err := json.Marshal(log)
	if err != nil {
		return false, fmt.Errorf("failed to marshal log: %w", err)
	}

	// Verify signature
	valid := ed25519.Verify(ed25519.PublicKey(publicKey), canonical, signature)
	return valid, nil
}

// GetPublicKey returns the base64-encoded public key
func (s *AuditSigner) GetPublicKey() string {
	return base64.StdEncoding.EncodeToString(s.publicKey)
}
