//! WiFi interface management

use anyhow::{Result, Context};
use std::process::Command;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WifiInterface {
    pub name: String,
    pub is_monitor_mode: bool,
    pub is_up: bool,
    pub mac_address: Option<String>,
    pub driver: Option<String>,
}

pub struct InterfaceManager;

impl InterfaceManager {
    pub fn new() -> Self {
        Self
    }

    /// List all available WiFi interfaces
    pub fn list_interfaces(&self) -> Result<Vec<WifiInterface>> {
        #[cfg(target_os = "linux")]
        {
            self.list_interfaces_linux()
        }

        #[cfg(target_os = "macos")]
        {
            self.list_interfaces_macos()
        }

        #[cfg(not(any(target_os = "linux", target_os = "macos")))]
        {
            anyhow::bail!("WiFi scanning is only supported on Linux and macOS")
        }
    }

    #[cfg(target_os = "linux")]
    fn list_interfaces_linux(&self) -> Result<Vec<WifiInterface>> {
        let output = Command::new("iw")
            .args(&["dev"])
            .output()
            .context("Failed to execute 'iw dev' command")?;

        if !output.status.success() {
            anyhow::bail!("iw command failed: {}", String::from_utf8_lossy(&output.stderr));
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let mut interfaces = Vec::new();
        let mut current_interface: Option<String> = None;

        for line in stdout.lines() {
            let line = line.trim();
            
            if line.starts_with("Interface ") {
                if let Some(name) = line.strip_prefix("Interface ") {
                    current_interface = Some(name.to_string());
                }
            } else if line.starts_with("type ") && current_interface.is_some() {
                let name = current_interface.take().unwrap();
                let is_monitor = line.contains("monitor");
                
                interfaces.push(WifiInterface {
                    name: name.clone(),
                    is_monitor_mode: is_monitor,
                    is_up: true, // Will be determined separately
                    mac_address: None,
                    driver: None,
                });
            }
        }

        Ok(interfaces)
    }

    #[cfg(target_os = "macos")]
    fn list_interfaces_macos(&self) -> Result<Vec<WifiInterface>> {
        let output = Command::new("networksetup")
            .args(&["-listallhardwareports"])
            .output()
            .context("Failed to execute networksetup command")?;

        if !output.status.success() {
            anyhow::bail!("networksetup command failed");
        }

        let stdout = String::from_utf8_lossy(&output.stdout);
        let mut interfaces = Vec::new();

        for section in stdout.split("\n\n") {
            if section.contains("Wi-Fi") || section.contains("AirPort") {
                for line in section.lines() {
                    if line.starts_with("Device: ") {
                        if let Some(name) = line.strip_prefix("Device: ") {
                            interfaces.push(WifiInterface {
                                name: name.to_string(),
                                is_monitor_mode: false,
                                is_up: true,
                                mac_address: None,
                                driver: None,
                            });
                        }
                    }
                }
            }
        }

        Ok(interfaces)
    }

    /// Enable monitor mode on an interface (Linux only)
    #[cfg(target_os = "linux")]
    pub fn enable_monitor_mode(&self, interface: &str) -> Result<()> {
        // Bring interface down
        Command::new("ip")
            .args(&["link", "set", interface, "down"])
            .output()
            .context("Failed to bring interface down")?;

        // Set monitor mode
        Command::new("iw")
            .args(&[interface, "set", "monitor", "control"])
            .output()
            .context("Failed to set monitor mode")?;

        // Bring interface up
        Command::new("ip")
            .args(&["link", "set", interface, "up"])
            .output()
            .context("Failed to bring interface up")?;

        Ok(())
    }

    /// Disable monitor mode (Linux only)
    #[cfg(target_os = "linux")]
    pub fn disable_monitor_mode(&self, interface: &str) -> Result<()> {
        Command::new("ip")
            .args(&["link", "set", interface, "down"])
            .output()?;

        Command::new("iw")
            .args(&[interface, "set", "type", "managed"])
            .output()?;

        Command::new("ip")
            .args(&["link", "set", interface, "up"])
            .output()?;

        Ok(())
    }

    /// Check if interface is in monitor mode
    pub fn is_monitor_mode(&self, interface: &str) -> Result<bool> {
        #[cfg(target_os = "linux")]
        {
            let output = Command::new("iw")
                .args(&["dev", interface, "info"])
                .output()?;

            let stdout = String::from_utf8_lossy(&output.stdout);
            Ok(stdout.contains("type monitor"))
        }

        #[cfg(not(target_os = "linux"))]
        {
            Ok(false)
        }
    }

    /// Get interface details
    pub fn get_interface_info(&self, interface: &str) -> Result<WifiInterface> {
        let is_monitor = self.is_monitor_mode(interface).unwrap_or(false);

        Ok(WifiInterface {
            name: interface.to_string(),
            is_monitor_mode: is_monitor,
            is_up: true,
            mac_address: None,
            driver: None,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_list_interfaces() {
        let manager = InterfaceManager::new();
        let result = manager.list_interfaces();
        
        // Should not fail even if no interfaces found
        assert!(result.is_ok());
    }
}
