//! Packet capture functionality

use anyhow::Result;

pub struct PacketCapture {
    interface: String,
}

impl PacketCapture {
    pub fn new(interface: String) -> Self {
        Self { interface }
    }

    pub async fn start_capture(&mut self) -> Result<()> {
        // TODO: Implement packet capture
        Ok(())
    }
}
