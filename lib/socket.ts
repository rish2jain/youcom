"use client";

import { io, Socket } from "socket.io-client";

// Get socket URL, handling Docker hostname for browser access
const getSocketUrl = () => {
  const envUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";
  // Browser can't access Docker hostnames, replace with localhost
  if (envUrl.includes("backend:")) {
    return envUrl.replace("backend:", "localhost:");
  }
  return envUrl;
};

const SOCKET_URL = getSocketUrl();

let socket: Socket | null = null;

export function getSocket(): Socket {
  if (!socket) {
    socket = io(SOCKET_URL, {
      transports: ["websocket"],
      path: "/socket.io",
      autoConnect: true,
    });
  }

  return socket;
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}
