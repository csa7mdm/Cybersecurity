FROM rust:1.75-alpine AS builder

WORKDIR /app

# Install dependencies
RUN apk add --no-cache \
    musl-dev \
    openssl-dev \
    libpcap-dev \
    linux-headers

# Copy manifests
COPY Cargo.toml Cargo.lock ./

# Build dependencies (cache layer)
RUN mkdir src && \
    echo "fn main() {}" > src/main.rs && \
    cargo build --release && \
    rm -rf src

# Copy source code
COPY src ./src

# Build application
RUN cargo build --release

# Runtime stage
FROM alpine:latest

RUN apk add --no-cache \
    libgcc \
    openssl \
    libpcap

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/cyper-core /usr/local/bin/

# Create necessary directories
RUN mkdir -p /scans /var/log/cyper

EXPOSE 9090

CMD ["cyper-core"]
