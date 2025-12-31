package brain

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"go.uber.org/zap"
)

type Client struct {
	baseURL    string
	httpClient *http.Client
	logger     *zap.Logger
}

func NewClient(url string, logger *zap.Logger) *Client {
	return &Client{
		baseURL: url,
		httpClient: &http.Client{
			Timeout: 60 * time.Second, // PDF generation might take time
		},
		logger: logger,
	}
}

type ScanResults map[string]interface{}
type AnalysisResult map[string]interface{}

type GenerateReportRequest struct {
	ScanResults ScanResults            `json:"scan_results"`
	ReportType  string                 `json:"report_type"`
	Format      string                 `json:"format"`
	Analysis    AnalysisResult         `json:"analysis,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

type GenerateReportResponse struct {
	Path   string `json:"path"`
	Status string `json:"status"`
	Report string `json:"report"` // Markdown content
}

func (c *Client) GenerateReport(req GenerateReportRequest) (*GenerateReportResponse, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	url := fmt.Sprintf("%s/api/v1/report", c.baseURL)
	resp, err := c.httpClient.Post(url, "application/json", bytes.NewBuffer(body))
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("brain service returned status: %d", resp.StatusCode)
	}

	var result GenerateReportResponse
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	return &result, nil
}
