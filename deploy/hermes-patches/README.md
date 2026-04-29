## Required server-side wiring (one-time, not idempotent in apply.sh)

Patch 08 needs Hermes to know how to call back into Django. After
the patch lands on the server, add these env vars to the Hermes
systemd unit:

```ini
# /home/admin/.config/systemd/user/hermes-gateway.service
Environment="HERMES_INTERNAL_TOKEN=<same value as Django HERMES_INTERNAL_TOKEN in backend/.env>"
Environment="DJANGO_BASE_URL=http://127.0.0.1:8004"
```

And add a TCP bind to the Django gunicorn so Hermes can reach it on
loopback (the unix socket is fine for nginx but awkward from aiohttp):

```ini
# /etc/systemd/system/gunicorn.service ExecStart=
gunicorn ... --bind unix:/home/admin/KitchenBook/backend/gunicorn.sock --bind 127.0.0.1:8004 ...
```

Then `systemctl --user daemon-reload && systemctl --user restart hermes-gateway`
and `sudo systemctl daemon-reload && sudo systemctl restart gunicorn`.
