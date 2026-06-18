# bledom-cli

Contrôle un ruban LED BLE type ELK-BLEDOM / BLEDOM / MELK depuis une interface web mobile-friendly, via une API REST locale (FastAPI + bleak).

---

## Prérequis

- Python 3.11+
- Bluetooth activé sur la machine
- Téléphone sur le même réseau Wi-Fi que le serveur

---

## Lancement rapide (Mac)

```bash
./run.sh
```

Le script crée un venv, installe les dépendances et démarre le serveur.  
L'URL locale pour ton téléphone s'affiche au démarrage, ex. :

```
http://192.168.1.42:8000
```

---

## Première connexion

1. Ouvre l'URL dans le navigateur de ton téléphone
2. Tape **Scanner les appareils** — attend ~6 secondes
3. Sélectionne ton ruban dans la liste et tape **Connecter**
4. L'adresse est sauvegardée dans `config.json` — reconnexion automatique au prochain démarrage

---

## API REST

| Méthode | Route | Body | Description |
|---------|-------|------|-------------|
| GET | `/scan` | — | Liste les appareils BLE compatibles |
| POST | `/connect` | `{"address": "XX:XX:XX:XX:XX:XX"}` | Connecte et persiste l'adresse |
| GET | `/status` | — | État connexion + dernière couleur/luminosité |
| POST | `/power` | `{"on": true}` | Allume / éteint |
| POST | `/color` | `{"r": 255, "g": 0, "b": 128}` | Couleur RGB |
| POST | `/brightness` | `{"value": 80}` | Luminosité 0–100 |

Documentation interactive : `http://localhost:8000/docs`

---

## Structure du projet

```
bledom-cli/
├── bledom/
│   ├── protocol.py     # bytes des commandes ELK-BLEDOM
│   ├── connection.py   # gestion BLE + reconnexion auto
│   ├── config.py       # persistance JSON
│   └── api.py          # routes FastAPI
├── static/
│   └── index.html      # UI mobile (Tailwind CDN)
├── main.py
├── requirements.txt
├── run.sh
└── config.json         # généré au premier /connect (gitignored)
```

---

## Dépannage BLE sur macOS

Si le scan ne trouve rien ou que la connexion échoue silencieusement :

1. **Autoriser Bluetooth** : Réglages Système → Confidentialité et sécurité → Bluetooth → autoriser le Terminal (ou iTerm, VS Code, etc.)
2. Désactiver/réactiver Bluetooth
3. Relancer le script

Sur macOS le backend bleak utilise CoreBluetooth — aucune dépendance system supplémentaire n'est requise.

---

## UUIDs du protocole

Les UUIDs utilisés (sources : intégration HA `led-ble` et composant custom `zengge`) :

| Rôle | UUID |
|------|------|
| Write (commandes) | `0000fff3-0000-1000-8000-00805f9b34fb` |
| Notify (état) | `0000fff4-0000-1000-8000-00805f9b34fb` |

Si ton appareil ne répond pas, lance un scan verbose pour inspecter ses caractéristiques :

```python
from bleak import BleakClient, BleakScanner
import asyncio

async def inspect(address):
    async with BleakClient(address) as c:
        for s in c.services:
            for ch in s.characteristics:
                print(ch.uuid, ch.properties)

asyncio.run(inspect("XX:XX:XX:XX:XX:XX"))
```

---

## Migration vers Linux (systemd)

Sur ton serveur Linux, copie le repo tel quel — aucune dépendance macOS dans le code.  
Pour le lancer comme service :

```ini
# /etc/systemd/system/bledom.service
[Unit]
Description=bledom-cli BLE LED server
After=network.target bluetooth.target

[Service]
Type=simple
WorkingDirectory=/opt/bledom-cli
ExecStart=/opt/bledom-cli/.venv/bin/python main.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now bledom
```

> Sur Linux, bleak utilise BlueZ. Assure-toi que `bluetoothd` tourne et que l'utilisateur est dans le groupe `bluetooth`.

---

## Token d'auth (optionnel, futur)

Le serveur n'a pas d'auth pour l'instant (usage local uniquement).  
Pour ajouter un token simple, il suffira d'un middleware FastAPI vérifiant un header `X-Token` lu depuis une variable d'environnement — prévu mais non implémenté.
