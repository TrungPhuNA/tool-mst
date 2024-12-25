# Clear dockẻ
```bash 
# Dừng và xóa tất cả container
docker stop $(docker ps -aq) && docker rm $(docker ps -aq)

# Xóa toàn bộ image, volume, và network (tùy chọn)
docker rmi $(docker images -q) -f
docker volume rm $(docker volume ls -q)
docker network rm $(docker network ls -q)

# Dọn dẹp hệ thống Docker
docker system prune -a --volumes

# Khởi động lại container từ Docker Compose
docker compose up -d

# Kiểm tra trạng thái
docker ps

# Don dẹp chrome
docker exec -it chrome bash
ps aux
docker stop chrome
docker start chrome

# Theo dõi tài nguyên có đc giải phóng không  
docker stats
```