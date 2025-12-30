//! WiFi security scanning module

use anyhow::{Result, Context};
use serde::{Deserialize, Serialize};
use std::process::Command;
use std::time::Duration;
use tokio::time::sleep;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Network {
    pub ssid: String,
    pub bssid: String,
    pub channel: u8,
    pub frequency: u32,
    pub signal_strength: i16,
    pub security_type: SecurityType,
    pub encryption: Option<String>,
    pub authentication: Option<String>,
    pub wps_enabled: bool,
    pub wps_locked: bool,
    pub hidden: bool,
    pub clients: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SecurityType {
    Open,
    WEP,
    WPA,
    WPA2,
    WPA3,
    WPA2WPA3, // Mixed mode
    Unknown,
}

impl SecurityType {
    pub fn from_str(s: &str) -> Self {
        let s_lower = s.to_lowercase();
        if s_lower.contains("wpa3") && s_lower.contains("wpa2") {
            SecurityType::WPA2WPA3
        } else if s_lower.contains("wpa3") {
            SecurityType::WPA3
        } else if s_lower.contains("wpa2") {
            SecurityType::WPA2
        } else if s_lower.contains("wpa") {
            SecurityType::WPA
        } else if s_lower.contains("wep") {
            SecurityType::WEP
        } else if s_lower.contains("open") {
            SecurityType::Open
        } else {
            SecurityType::Unknown
        }
    }

    pub fn security_level(&self) -> u8 {
        match self {
            SecurityType::Open => 0,
            SecurityType::WEP => 1,
            SecurityType::WPA => 2,
            SecurityType::WPA2 => 3,
            SecurityType::WPA2WPA3 => 4,
            SecurityType::WPA3 => 5,
            SecurityType::Unknown => 0,
        }
    }
}

pub struct WiFiScanner {
    interface: String,
    scan_duration: Duration,
}

impl WiFiScanner {
    pub fn new(interface: String) -> Self {
        Self {
            interface,
            scan_duration: Duration::from_secs(10),
        }
    }

    pub fn with_duration(mut self, duration: Duration) -> Self {
        self.scan_duration = duration;
        self
    }

    /// Perform passive WiFi scan
    pub async fn scan_networks(&self) -> Result<Vec<Network>> {
        #[cfg(target_os = "linux")]
        {
            self.scan_networks_linux().await
        }

        #[cfg(target_os = "macos")]
        {
            self.scan_networks_macos().await
        }

        #[cfg(not(any(target_os = "linux", target_os = "macos")))]
        {
            anyhow::bail!("WiFi scanning is only supported on Linux and macOS")
        }
    }

    #[cfg(target_os = "linux")]
    async fn scan_networks_linux(&self) -> Result<Vec<Network>> {
        // Trigger scan
        let _output = Command::new("iw")
            .args(&[&self.interface, "scan"])
            .output()
            .context("Failed to trigger WiFi scan")?;

        // Wait for scan to complete
        sleep(self.scan_duration).await;

        // Get scan results
        let output = Command::new("iw")
            .args(&[&self.interface, "scan", "dump"])
            .output()
            .context("Failed to get scan results")?;

        if !output.status.success() {
            anyhow::bail!("Scan failed: {}", String::from_utf8_lossy(&output.stderr));
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let networks = self.parse_iw_scan_results(&stdout)?;

        Ok(networks)
    }

    #[cfg(target_os = "macos")]
    async fn scan_networks_macos(&self) -> Result<Vec<Network>> {
        let output = Command::new("/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport")
            .args(&["-s"])
            .output()
            .context("Failed to scan WiFi networks")?;

        if !output.status.success() {
            anyhow::bail!("WiFi scan failed");
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let networks = self.parse_airport_results(&stdout)?;

        Ok(networks)
    }

    fn parse_iw_scan_results(&self, output: &str) -> Result<Vec<Network>> {
        let mut networks = Vec::new();
        let mut current_network: Option<Network> = None;

        for line in output.lines() {
            let line = line.trim();

            if line.starts_with("BSS ") {
                // Save previous network
                if let Some(network) = current_network.take() {
                    networks.push(network);
                }

                // Start new network
                if let Some(bssid) = line.strip_prefix("BSS ").and_then(|s| s.split('(').next()) {
                    current_network = Some(Network {
                        ssid: String::new(),
                        bssid: bssid.trim().to_string(),
                        channel: 0,
                        frequency: 0,
                        signal_strength: -100,
                        security_type: SecurityType::Unknown,
                        encryption: None,
                        authentication: None,
                        wps_enabled: false,
                        wps_locked: false,
                        hidden: false,
                        clients: Vec::new(),
                    });
                }
            } else if let Some(ref mut network) = current_network {
                if line.starts_with("SSID: ") {
                    network.ssid = line.strip_prefix("SSID: ").unwrap_or("").to_string();
                    network.hidden = network.ssid.is_empty();
                } else if line.starts_with("freq: ") {
                    if let Ok(freq) = line.strip_prefix("freq: ").unwrap_or("0").parse() {
                        network.frequency = freq;
                        network.channel = self.frequency_to_channel(freq);
                    }
                } else if line.starts_with("signal: ") {
                    if let Some(signal_str) = line.strip_prefix("signal: ") {
                        if let Some(signal) = signal_str.split_whitespace().next() {
                            network.signal_strength = signal.parse().unwrap_or(-100);
                        }
                    }
                } else if line.contains("RSN:") || line.contains("WPA:") {
                    if line.contains("WPA3") {
                        network.security_type = SecurityType::WPA3;
                    } else if line.contains("WPA2") || line.contains("RSN") {
                        network.security_type = SecurityType::WPA2;
                    } else {
                        network.security_type = SecurityType::WPA;
                    }
                } else if line.contains("WEP") {
                    network.security_type = SecurityType::WEP;
                } else if line.contains("WPS:") {
                    network.wps_enabled = true;
                }
            }
        }

        // Save last network
        if let Some(network) = current_network {
            networks.push(network);
        }

        Ok(networks)
    }

    #[cfg(target_os = "macos")]
    fn parse_airport_results(&self, output: &str) -> Result<Vec<Network>> {
        let mut networks = Vec::new();

        for (i, line) in output.lines().enumerate() {
            if i == 0 {
                continue; // Skip header
            }

            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 3 {
                continue;
            }

            let ssid = parts[0].to_string();
            let bssid = parts.get(1).unwrap_or(&"").to_string();
            let signal_strength: i16 = parts.get(2).and_then(|s| s.parse().ok()).unwrap_or(-100);
            
            let security_info = parts.get(6..).map(|s| s.join(" ")).unwrap_or_default();
            let security_type = SecurityType::from_str(&security_info);

            networks.push(Network {
                ssid,
                bssid,
                channel: 0,
                frequency: 0,
                signal_strength,
                security_type,
                encryption: None,
                authentication: None,
                wps_enabled: false,
                wps_locked: false,
                hidden: false,
                clients: Vec::new(),
            });
        }

        Ok(networks)
    }

    /// Analyze security of a network
    pub async fn analyze_security(&self, network: &Network) -> Result<SecurityReport> {
        let mut report = SecurityReport {
            wps_enabled: network.wps_enabled,
            crackability_score: 0,
            estimated_crack_time: String::new(),
            vulnerabilities: Vec::new(),
            recommendations: Vec::new(),
        };

        // Security level analysis
        let security_level = network.security_type.security_level();

        // Calculate crackability score (0-100, higher = easier to crack)
        report.crackability_score = match network.security_type {
            SecurityType::Open => 100,
            SecurityType::WEP => 95,
            SecurityType::WPA => 70,
            SecurityType::WPA2 => {
                if network.wps_enabled {
                    80
                } else {
                    30
                }
            }
            SecurityType::WPA2WPA3 => 20,
            SecurityType::WPA3 => 10,
            SecurityType::Unknown => 50,
        };

        // Estimate crack time
        report.estimated_crack_time = match network.security_type {
            SecurityType::Open => "Immediate (no encryption)".to_string(),
            SecurityType::WEP => "Minutes to hours".to_string(),
            SecurityType::WPA if network.wps_enabled => "Hours (via WPS PIN)".to_string(),
            SecurityType::WPA => "Days to weeks (dictionary attack)".to_string(),
            SecurityType::WPA2 if network.wps_enabled => "Hours to days (via WPS)".to_string(),
            SecurityType::WPA2 => "Weeks to months (with weak password)".to_string(),
            SecurityType::WPA2WPA3 => "Months to years (strong password required)".to_string(),
            SecurityType::WPA3 => "Years to impractical (current technology)".to_string(),
            SecurityType::Unknown => "Unable to estimate".to_string(),
        };

        // Identify vulnerabilities
        if network.security_type == SecurityType::Open {
            report.vulnerabilities.push("No encryption - all traffic visible".to_string());
            report.recommendations.push("Enable WPA3 or at minimum WPA2".to_string());
        }

        if network.security_type == SecurityType::WEP {
            report.vulnerabilities.push("WEP encryption is broken and easily cracked".to_string());
            report.recommendations.push("Upgrade to WPA2 or WPA3 immediately".to_string());
        }

        if network.wps_enabled {
            report.vulnerabilities.push("WPS enabled - vulnerable to brute force PIN attacks".to_string());
            report.recommendations.push("Disable WPS in router settings".to_string());
        }

        if network.security_type == SecurityType::WPA {
            report.vulnerabilities.push("WPA (TKIP) has known weaknesses".to_string());
            report.recommendations.push("Upgrade to WPA2 (AES) or WPA3".to_string());
        }

        if network.hidden {
            report.recommendations.push("Hidden SSID provides minimal security - still detectable".to_string());
        }

        // General recommendations
        if security_level < 4 {
            report.recommendations.push("Use a strong, unique password (16+ characters)".to_string());
            report.recommendations.push("Consider upgrading to WPA3 if supported".to_string());
        }

        Ok(report)
    }

    fn frequency_to_channel(&self, frequency: u32) -> u8 {
        match frequency {
            2412 => 1,
            2417 => 2,
            2422 => 3,
            2427 => 4,
            2432 => 5,
            2437 => 6,
            2442 => 7,
            2447 => 8,
            2452 => 9,
            2457 => 10,
            2462 => 11,
            2467 => 12,
            2472 => 13,
            2484 => 14,
            // 5GHz
            5180 => 36,
            5200 => 40,
            5220 => 44,
            5240 => 48,
            _ => 0,
        }
    }
}

#[derive(Debug, Default, Serialize, Deserialize)]
pub struct Security Report {
    pub wps_enabled: bool,
    pub crackability_score: u8,
    pub estimated_crack_time: String,
    pub vulnerabilities: Vec<String>,
    pub recommendations: Vec<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_security_type_levels() {
        assert_eq!(SecurityType::Open.security_level(), 0);
        assert_eq!(SecurityType::WEP.security_level(), 1);
        assert_eq!(SecurityType::WPA.security_level(), 2);
        assert_eq!(SecurityType::WPA2.security_level(), 3);
        assert_eq!(SecurityType::WPA3.security_level(), 5);
    }

    #[test]
    fn test_security_type_from_str() {
        assert_eq!(SecurityType::from_str("WPA3"), SecurityType::WPA3);
        assert_eq!(SecurityType::from_str("WPA2"), SecurityType::WPA2);
        assert_eq!(SecurityType::from_str("WPA"), SecurityType::WPA);
        assert_eq!(SecurityType::from_str("WEP"), SecurityType::WEP);
        assert_eq!(SecurityType::from_str("Open"), SecurityType::Open);
    }
}
