import socket
import threading
import queue
import sys

CLIENT_PORT = 11434
TUNNEL_PORT = 41030

tunnel_queue = queue.Queue()

def pipe_sockets(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try:
            src.close()
        except Exception:
            pass
        try:
            dst.close()
        except Exception:
            pass

def handle_client(client_socket):
    try:
        # Get a tunnel socket from the queue (timeout after 5 seconds)
        tunnel_socket = tunnel_queue.get(timeout=5.0)
    except queue.Empty:
        print("No available tunnel sockets from Windows!")
        client_socket.close()
        return

    # Pipe client <-> tunnel
    t1 = threading.Thread(target=pipe_sockets, args=(client_socket, tunnel_socket), daemon=True)
    t2 = threading.Thread(target=pipe_sockets, args=(tunnel_socket, client_socket), daemon=True)
    t1.start()
    t2.start()

def start_client_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('127.0.0.1', CLIENT_PORT))
    except Exception as e:
        print(f"Failed to bind to 127.0.0.1:{CLIENT_PORT}: {e}")
        sys.exit(1)
    server.listen(128)
    print(f"WSL: Listening for Ollama clients on 127.0.0.1:{CLIENT_PORT}")

    while True:
        try:
            client_sock, addr = server.accept()
            threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()
        except Exception as e:
            print(f"Error accepting client: {e}")

def start_tunnel_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('0.0.0.0', TUNNEL_PORT))
    except Exception as e:
        print(f"Failed to bind to 0.0.0.0:{TUNNEL_PORT}: {e}")
        sys.exit(1)
    server.listen(128)
    print(f"WSL: Listening for Windows tunnel connections on 0.0.0.0:{TUNNEL_PORT}")

    while True:
        try:
            tunnel_sock, addr = server.accept()
            # Keep-alive on the tunnel socket
            tunnel_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            tunnel_queue.put(tunnel_sock)
        except Exception as e:
            print(f"Error accepting tunnel: {e}")

if __name__ == "__main__":
    t_tunnel = threading.Thread(target=start_tunnel_server, daemon=True)
    t_client = threading.Thread(target=start_client_server, daemon=True)
    t_tunnel.start()
    t_client.start()
    
    # Keep main thread alive
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping WSL tunnel.")
