//! Port scanning functionality

use anyhow::{Result, Context};
use std::net::{IpAddr, SocketAddr, TcpStream};
use std::time::Duration;
use tokio::net::UdpSocket;
use tokio::time::timeout;
use rayon::prelude::*;
use serde::{Deserialize, Serialize};

pub struct PortScanner {
    target: IpAddr,
    ports: PortRange,
    timeout_duration: Duration,
    max_parallel: usize,
}

pub struct PortRange {
    pub start: u16,
    pub end: u16,
}

impl PortScanner {
    pub fn new(target: IpAddr, start_port: u16, end_port: u16) -> Self {
        Self {
            target,
            ports: PortRange {
                start: start_port,
                end: end_port,
            },
            timeout_duration: Duration::from_millis(1000),
            max_parallel: 100,
        }
    }

    pub fn with_timeout(mut self, duration: Duration) -> Self {
        self.timeout_duration = duration;
        self
    }

    pub fn with_parallelism(mut self, max_parallel: usize) -> Self {
        self.max_parallel = max_parallel;
        self
    }

    /// Perform TCP SYN scan (requires root/admin privileges)
    pub async fn scan(&self) -> Result<Vec<PortResult>> {
        let ports: Vec<u16> = (self.ports.start..=self.ports.end).collect();
        
        // Use rayon for parallel scanning
        let results: Vec<PortResult> = ports
            .par_iter()
            .chunks(self.max_parallel)
            .flat_map(|port_chunk| {
                port_chunk
                    .iter()
                    .filter_map(|&&port| {
                        match self.scan_tcp_port(port) {
                            Ok(result) => Some(result),
                            Err(_) => None,
                        }
                    })
                    .collect::<Vec<_>>()
            })
            .collect();

        Ok(results)
    }

    /// Scan a single TCP port using connect scan
    fn scan_tcp_port(&self, port: u16) -> Result<PortResult> {
        let socket_addr = SocketAddr::new(self.target, port);
        
        match TcpStream::connect_timeout(&socket_addr, self.timeout_duration) {
            Ok(_stream) => {
                // Port is open
                let service = self.detect_service(port);
                Ok(PortResult {
                    port,
                    state: PortState::Open,
                    service,
                    protocol: Protocol::TCP,
                    banner: None,
                })
            }
            Err(_) => {
                // Port is closed or filtered
                Ok(PortResult {
                    port,
                    state: PortState::Closed,
                    service: None,
                    protocol: Protocol::TCP,
                    banner: None,
                })
            }
        }
    }

    /// Scan UDP port
    pub async fn scan_udp_port(&self, port: u16) -> Result<PortResult> {
        let socket = UdpSocket::bind("0.0.0.0:0").await
            .context("Failed to bind UDP socket")?;

        let target_addr = SocketAddr::new(self.target, port);

        // Send empty UDP packet
        socket.send_to(&[], target_addr).await?;

        // Try to receive response
        let mut buf = [0u8; 1024];
        let result = timeout(
            self.timeout_duration,
            socket.recv_from(&mut buf)
        ).await;

        let state = match result {
            Ok(Ok(_)) => PortState::Open,
            Ok(Err(_)) => PortState::Closed,
            Err(_) => PortState::OpenFiltered, // No response - could be open or filtered
        };

        Ok(PortResult {
            port,
            state,
            service: self.detect_service(port),
            protocol: Protocol::UDP,
            banner: None,
        })
    }

    /// Detect common services by port number
    fn detect_service(&self, port: u16) -> Option<String> {
        let service = match port {
            20 => "FTP-DATA",
            21 => "FTP",
            22 => "SSH",
            23 => "Telnet",
            25 => "SMTP",
            53 => "DNS",
            80 => "HTTP",
            110 => "POP3",
            143 => "IMAP",
            443 => "HTTPS",
            445 => "SMB",
            3306 => "MySQL",
            3389 => "RDP",
            5432 => "PostgreSQL",
            5900 => "VNC",
            6379 => "Redis",
            8080 => "HTTP-Proxy",
            8443 => "HTTPS-Alt",
            27017 => "MongoDB",
            _ => return None,
        };

        Some(service.to_string())
    }

    /// Perform banner grabbing on open port
    pub async fn grab_banner(&self, port: u16) -> Result<Option<String>> {
        let socket_addr = SocketAddr::new(self.target, port);
        
        match timeout(
            self.timeout_duration,
            TcpStream::connect(socket_addr)
        ).await {
            Ok(Ok(mut stream)) => {
                // Try to read banner
                use std::io::Read;
                stream.set_read_timeout(Some(self.timeout_duration))?;
                
                let mut buffer = [0u8; 1024];
                match stream.read(&mut buffer) {
                    Ok(n) if n > 0 => {
                        let banner = String::from_utf8_lossy(&buffer[..n]).to_string();
                        Ok(Some(banner))
                    }
                    _ => Ok(None)
                }
            }
            _ => Ok(None)
        }
    }

    /// Get scan statistics
    pub fn get_scan_info(&self) -> ScanInfo {
        let total_ports = (self.ports.end - self.ports.start + 1) as usize;
        let estimated_duration = Duration::from_millis(
            (total_ports as u64 * self.timeout_duration.as_millis() as u64) / self.max_parallel as u64
        );

        ScanInfo {
            target: self.target,
            port_range: format!("{}-{}", self.ports.start, self.ports.end),
            total_ports,
            estimated_duration_seconds: estimated_duration.as_secs(),
            max_parallel: self.max_parallel,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct PortResult {
    pub port: u16,
    pub state: PortState,
    pub service: Option<String>,
    pub protocol: Protocol,
    pub banner: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq)]
pub enum PortState {
    Open,
    Closed,
    Filtered,
    OpenFiltered,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub enum Protocol {
    TCP,
    UDP,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ScanInfo {
    pub target: IpAddr,
    pub port_range: String,
    pub total_ports: usize,
    pub estimated_duration_seconds: u64,
    pub max_parallel: usize,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::str::FromStr;

    #[test]
    fn test_port_range() {
        let scanner = PortScanner::new(
            IpAddr::from_str("127.0.0.1").unwrap(),
            1,
            100
        );
        
        assert_eq!(scanner.ports.start, 1);
        assert_eq!(scanner.ports.end, 100);
    }

    #[test]
    fn test_service_detection() {
        let scanner = PortScanner::new(
            IpAddr::from_str("127.0.0.1").unwrap(),
            1,
            100
        );

        assert_eq!(scanner.detect_service(80), Some("HTTP".to_string()));
        assert_eq!(scanner.detect_service(443), Some("HTTPS".to_string()));
        assert_eq!(scanner.detect_service(22), Some("SSH".to_string()));
        assert_eq!(scanner.detect_service(99999), None);
    }

    #[tokio::test]
    async fn test_scan_info() {
        let scanner = PortScanner::new(
            IpAddr::from_str("127.0.0.1").unwrap(),
            1,
            1000
        );

        let info = scanner.get_scan_info();
        assert_eq!(info.total_ports, 1000);
        assert_eq!(info.port_range, "1-1000");
    }
}
