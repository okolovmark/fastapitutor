import os


def generate_nginx_conf():
    nginx_dir = ".nginx"
    nginx_log_dir = os.path.join(nginx_dir, "logs")
    conf_path = os.path.join(nginx_dir, "nginx.conf")

    os.makedirs(nginx_dir, exist_ok=True)
    os.makedirs(nginx_log_dir, exist_ok=True)

    if os.path.exists(conf_path):
        print(f"nginx.conf already exists at {conf_path}")
        return

    http_port = os.getenv('FASTAPI_PORT', '')
    nginx_port = os.getenv('NGINX_PORT', '')
    
    config_content = """error_log logs/error.log;
pid logs/nginx.pid;

events {
    worker_connections 1024;
}

http {
    upstream backend {
        server 127.0.0.1:HTTP_PORT;
    }

    server {
        listen NGINX_PORT so_keepalive=on;
        server_name localhost;
        # Log files
        access_log logs/access.log;
        error_log logs/error.log;

        # Increase proxy buffer size
        proxy_buffers 16 64k;
        proxy_buffer_size 128k;
        # Force timeouts if the backend dies
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        # Enable data compression
        gzip on;
        gzip_min_length 1100;
        gzip_buffers 4 32k;
        gzip_types text/plain text/xml text/css text/less application/x-javascript application/xml application/json application/javascript;
        gzip_vary on;

        # Cache static data
        location ~* /web/static/ {
            proxy_cache_valid 200 60m;
            proxy_buffering on;
            expires 864000;
            proxy_pass http://backend;
        }

        location / {
                proxy_pass http://backend;
                # The following makes the timeout broader
                proxy_read_timeout 30000;
                proxy_redirect off;
        }
    }
}""".replace('HTTP_PORT', http_port).replace('NGINX_PORT', nginx_port)
    
    # Write configuration to file
    with open(conf_path, 'w') as f:
        f.write(config_content)
    
    print(f"Generated nginx.conf with ports: FastAPI HTTP={http_port}, Nginx={nginx_port}")

if __name__ == '__main__':
    generate_nginx_conf()