# Acesso ao robô pelo cabo ethernet

**Data:** 2026-11-16
**Objetivo:** do PC do laboratório, entrar no robô com `ssh robo`, sempre pelo mesmo cabo e pelo mesmo IP.

**Situação:** o IP do robô é `192.168.185.3` e o usuário é `ubuntu`. Os passos 1 a 3 foram feitos e confirmados em 2026-11-16: `ping` e `ssh robo` funcionam pelo cabo. O acesso sem cabo está na última seção. O PC do lab está no Wi-Fi `192.168.7.0/24`, e o robô fica em outra sub-rede (`192.168.185.x`). Sem o passo 1, o PC não tem rota até ele e o `ping` falha com 100% de perda.

## 1. IP fixo na porta ethernet do PC (uma vez só)

Rode no terminal do PC, em qualquer pasta. Isso cria um perfil permanente do NetworkManager para a placa `enp86s0`. Quando o cabo é ligado, o PC usa `192.168.185.10` e passa a enxergar a rede do robô.

```
sudo nmcli con add type ethernet ifname enp86s0 con-name robo-cabo \
  ipv4.method manual ipv4.addresses 192.168.185.10/24 \
  ipv4.never-default yes connection.autoconnect yes
sudo nmcli con up robo-cabo
```

- `192.168.185.10`: endereço livre na mesma sub-rede do robô.
- `never-default`: o cabo não pode virar a rota de internet. O Wi-Fi continua sendo a saída.
- Para desfazer: `sudo nmcli con delete robo-cabo`.

## 2. Apelido `robo` no SSH

O arquivo é `~/.ssh/config` (`/home/robotica/.ssh/config`). Crie e edite:

```
mkdir -p ~/.ssh
nano ~/.ssh/config
```

Conteúdo (salvar com `Ctrl+O`, `Enter`, sair com `Ctrl+X`):

```
Host robo
    HostName 192.168.185.3
    User ubuntu
```

Depois, `chmod 600 ~/.ssh/config`, porque o SSH exige essa permissão.

## 3. Teste

```
ping 192.168.185.3
ssh robo
```

O `ssh robo` continua pedindo a senha do robô. Não usamos chave SSH de propósito.

## Se não funcionar

- `ping` sem resposta: o cabo precisa estar ligado nos dois lados. Confira com `ip -br addr` se a `enp86s0` está `UP` e tem `192.168.185.10`.
- O robô pode ter outro IP no cabo. Descubra pelo próprio robô (`ip -br addr`) e troque o IP no `HostName` e a sub-rede no passo 1.
- Depois do SSH, o ROS ainda precisa que o `ROS_DOMAIN_ID` e o discovery batam (`infra/lab/rede_lab.env`). Teste com `infra/docker/lab.sh robo checar-rede`.

## Conectar ao robô sem cabo (Wi-Fi)

**Situação (2026-11-16):** feito e testado. O robô está no Wi-Fi `PixelLab-2.4GHz` com o IP `192.168.7.7` (DHCP), e o PC entra com `ssh robo-wifi`. A conexão ficou estável por 2 minutos, com ping nos dois sentidos. **Não testado:** se o robô reconecta sozinho depois de reiniciar, e se o IP se mantém.

### O que deu certo

1. Entrar pelo cabo (`ssh robo`) e configurar o Wi-Fi do robô como cliente (`Wi-Fi Mode: Client`, `DHCP: True`). O menu do `turtlebot4-setup` desta versão tem: Wi-Fi Mode, SSID, Password, Band, IP Address e DHCP. Não há campo de Regulatory Domain.
2. Usar a rede **`PixelLab-2.4GHz`**, e não a `PixelLab-5GHz` (ver a seção abaixo). A senha é a mesma das duas, mas não fica neste documento. Peça à equipe do INF.
3. No robô, o perfil foi criado direto pelo NetworkManager, sem o menu:
   ```
   sudo nmcli device wifi connect "PixelLab-2.4GHz" password '<senha>' ifname wlan0
   ```
   Com aspas simples em volta da senha, porque ela tem `!`.
4. Do PC, ainda com o cabo: `ping 192.168.7.7`, e depois o apelido em `~/.ssh/config`:
   ```
   Host robo-wifi
       HostName 192.168.7.7
       User ubuntu
   ```
5. Tirar o cabo e rodar `ssh robo-wifi`.

### Por que não o `PixelLab-5GHz`

O robô conectava nos 5 GHz logo depois de ligar e caía cerca de 20 s depois (`CTRL-EVENT-DISCONNECTED ... locally_generated`), e depois não achava mais a rede (`ssid-not-found`). A lista de redes que o robô enxerga tem canais de 5 GHz até o 140, mas nenhum acima do 149, e a `PixelLab-5GHz` fica no canal 157. Fixar o país `BR` (`/etc/modprobe.d/cfg80211-br.conf`, com `options cfg80211 ieee80211_regdom=BR`) mudou o domínio regulatório do kernel, mas **não resolveu**: o canal 157 continuou invisível. A causa real não foi descoberta. O 2,4 GHz funcionou, e a causa do 5 GHz fica em aberto. O arquivo `cfg80211-br.conf` continua no robô, é inofensivo e pode ser removido com `sudo rm /etc/modprobe.d/cfg80211-br.conf`.

### Cuidados

- **IP pode mudar:** o `192.168.7.7` vem do DHCP. Peça ao responsável pelo roteador uma reserva de DHCP para o robô. Sem ela, o `robo-wifi` pode parar de funcionar, e o jeito de descobrir o IP novo é entrar pelo cabo e rodar `ip -br addr`.
- **`turtlebot4-setup`:** o perfil do 2,4 GHz foi criado fora do `/etc/netplan/50-wifis.yaml` (que o próprio `turtlebot4-setup` gera e avisa para não editar à mão). Se alguém rodar Apply Settings de novo, o netplan é recriado só com o 5 GHz. Nesse caso, troque o SSID para `PixelLab-2.4GHz` dentro do menu.
- **2,4 GHz:** tem menos banda que 5 GHz. Para `ssh` e o ROS costuma bastar. Vídeo da câmera pode pesar.
- **Isolamento de clientes:** alguns Wi-Fi institucionais impedem aparelhos de se enxergarem. Neste laboratório isso **não** aconteceu: o PC e o robô se alcançam.
- **ROS:** o `ssh` funcionando não basta para o ROS. Veja a seção abaixo.
- **Senha do `ssh`:** o robô ainda usa a senha padrão do `ubuntu`. Vale trocar com `passwd` no robô.
- **Autorização:** a mudança de Wi-Fi no robô (perfil `PixelLab-2.4GHz` e o arquivo `cfg80211-br.conf`) foi feita a pedido do Roberto, em 2026-11-16, como pede o `docs/contexto/AGENTES.md` (seção 1).

## ROS pelo Wi-Fi: rotas no PC

**Situação (2026-11-16):** feito e testado. Com as rotas na conexão `PixelLab-2.4GHz`, o `infra/docker/lab.sh robo checar-rede` deu `REDE OK`, e os tópicos `/robot1/scan`, `/robot1/odom` e `/robot1/battery_state` chegam ao PC.

O robô usa Discovery Server, e o DDS dele anuncia todos os endereços do robô: `192.168.7.7` (Wi-Fi), `192.168.185.3` (cabo) e `192.168.186.3` (USB com a Create 3, que fica em `192.168.186.2`). O PC responde em todos. Pelo Wi-Fi, as respostas para `192.168.185.x` e `192.168.186.x` vão para o roteador e se perdem. O PC nunca completa a descoberta e não vê nenhum tópico. Medido com `tcpdump`: em 20 s, o PC mandou 545 pacotes para cada um desses dois endereços e só 33 para o Wi-Fi do robô. O manual do TurtleBot 4 prevê a rota da `192.168.186.0/24` pelo IP do robô ([Discovery Server](https://turtlebot.github.io/turtlebot4-user-manual/setup/discovery_server.html)).

Rode uma vez no PC. A rota fica salva na conexão Wi-Fi:

```
sudo nmcli connection modify "PixelLab-2.4GHz" +ipv4.routes "192.168.186.0/24 192.168.7.7 500, 192.168.185.0/24 192.168.7.7 500"
sudo nmcli connection up "PixelLab-2.4GHz"
```

- **Qual conexão:** use o nome da rede em que o PC estiver (`nmcli -t -f NAME,DEVICE connection show --active`). A rota vale só naquela conexão. Se o PC alternar entre `PixelLab-2.4GHz` e `PixelLab-5GHz`, repita o comando para as duas.
- **Métrica 500:** com o cabo ligado, a rota direta da placa `enp86s0` (métrica menor) continua valendo para a `192.168.185.0/24`.
- **IP do robô:** se ele mudar, refaça as rotas com o IP novo e atualize o `ROS_DISCOVERY_SERVER` do `infra/lab/rede_lab.env`.
- **Desfazer:** troque `+ipv4.routes` por `-ipv4.routes` no mesmo comando.

Depois, o teste é `infra/docker/lab.sh robo checar-rede`, que confere as rotas antes de testar o DDS e, se faltarem, mostra este mesmo comando.

## Vários robôs

Cada robô tem um perfil em `infra/lab/robos/`, com namespace, domínio e servidor de descoberta. O que é igual para todos fica em `infra/lab/rede_lab.env`. Para trocar de robô:

```
infra/docker/lab.sh robo parar          # se houver serviços de outro robô no ar
infra/docker/lab.sh robo usar robot3    # ajusta as rotas do PC (sudo) e testa a rede
infra/docker/lab.sh robo usar           # mostra o robô em uso e os perfis
```

Depois do `usar`, o `lab.sh robo`, o `rodar.sh` e o preflight valem para o robô escolhido. A escolha fica em um arquivo local deste PC (ignorado pelo git). A variável `ROBO=<nome>`, quando definida no terminal, vale sobre ela. Sem as duas, vale o `robot1`.

O `usar` altera só as rotas das sub-redes `192.168.186.0/24` e `192.168.185.0/24` da conexão em uso, e só se o robô responder ao ping. Se as rotas já estiverem certas, não pede `sudo`. Ele não troca o Wi-Fi do PC.

| Perfil | Wi-Fi | IP (DHCP) | Servidor de descoberta | Série do Raspberry Pi |
|---|---|---|---|---|
| `robot1` | `PixelLab-2.4GHz` | `192.168.7.7` | id 1 | não anotado |
| `robot3` | `Robotica_Deco` | `192.168.68.53` | id 3 | `1000000044bad95f` |

- **Um robô por vez neste PC.** Com serviços de um robô no ar, o `lab.sh` recusa ações para outro.
- **Rotas:** todos os robôs usam as mesmas sub-redes internas, e uma conexão do PC só tem um caminho para cada uma. Por isso o `usar` troca as rotas ao alternar entre robôs do mesmo Wi-Fi.
- **Robô novo:** no robô, leia `cat /etc/turtlebot4/setup.bash`, `ip -br addr` e `grep '^Serial' /proc/cpuinfo`. No PC, copie um perfil existente e preencha. A quantidade de `;` antes do IP é o id do servidor: o mesmo que aparece no `ROS_DISCOVERY_SERVER` do robô.
