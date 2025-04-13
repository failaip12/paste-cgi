# Paste-cgi

```
server {

    server_name SERVERURL;
    root ROOTFOLDER;

    location / {
        auth_basic "Restricted Content"; # Basic Auth
        auth_basic_user_file /etc/nginx/.htpasswd; # Basic Auth
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME PATH TO SCRIPT;
        fastcgi_param PATH_INFO $uri;
        fastcgi_param QUERY_STRING $args;
        fastcgi_param HTTP_HOST $server_name;
        fastcgi_param CONTENT_LENGTH $content_length;
        fastcgi_param CONTENT_TYPE $content_type;
        fastcgi_param ALLOWED_DIR PATH WHERE THE ALLOWED DIRECTORY IS TO CHANGE FILES;
        fastcgi_pass unix:/run/fcgiwrap.socket;
    }


    listen [::]:443 ssl; # managed by Certbot
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/paste.cirakg.xyz/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/paste.cirakg.xyz/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot

}
server {
    if ($host = paste.cirakg.xyz) {
        return 301 https://$host$request_uri;
    } # managed by Certbot



    listen 80;
    listen [::]:80;

    server_name paste.cirakg.xyz;
    return 404; # managed by Certbot


}

```