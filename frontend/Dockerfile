# Use nginx to serve static files
FROM nginx:alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy static files
COPY . /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]