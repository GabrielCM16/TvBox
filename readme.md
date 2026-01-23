```python -m venv .env```
ativa o venv
 ```source .env/bin/activate```


instalar requeriments.txt

```pip install -r requirements.txt```

sudo apt update

```xargs -a apt-packages.txt sudo apt install -y```

arquivo editando gambiarra

```sudo nano /usr/local/lib/python3.7/dist-packages/neopixel_write.py```


## verificando se o getty está ativo
systemctl status serial-getty@ttyS2.service


## desabilitando
sudo systemctl stop serial-getty@ttyS2.service
sudo systemctl disable serial-getty@ttyS2.service
sudo systemctl mask serial-getty@ttyS2.service

## sudo nano /boot/armbianEnv.txt
console=tty1

