# Semana 2: ROS 2 em Python (8 horas)

## O que é esta semana

Fazer em Python o que você fez no terminal: um programa que lê um topic e outro que manda uma action e acompanha o progresso.

## Por que

O Navigator, o `patrol_loop` e o seu futuro nó com LLM são exatamente isso: um programa Python que lê a bateria (topic) e manda o robô ir a um lugar (action). Python você já domina. O que há de novo é só o modelo de callbacks e o empacotamento.

## Os conceitos novos

| Conceito | O que é | Comparação |
|---|---|---|
| `rclpy` | A biblioteca do ROS 2 para Python | Como `requests`, mas para ROS |
| Callback | Função que o ROS chama quando uma mensagem chega | Como um handler de rota em uma API web |
| `spin` | O laço que fica esperando e dispara callbacks | Como rodar um servidor. Sem ele, nenhum callback dispara |
| Package | Pasta com `package.xml` e `setup.py` | Como um pacote pip |
| `colcon build` | Compila o workspace | Como um `pip install -e` de vários pacotes |
| `source install/setup.bash` | Faz o terminal enxergar o que foi compilado | Como ativar um virtualenv. **Esquecer disso é o erro mais comum** |

## O que estudar (cerca de 2 horas)

| Ordem | Material | Foco |
|---|---|---|
| 1 | [Índice das bibliotecas cliente](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries.html): colcon e criar package | Faça. Ignore as páginas de C++ |
| 2 | [Publisher e subscriber em Python](https://docs.ros.org/en/jazzy/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html) | Digite o código, não copie |
| 3 | [Action server e client em Python](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/Writing-an-Action-Server-Client/Py.html) | **Foque no client.** Você quase nunca vai escrever um server |

Se a explicação oficial não entrar, tente o [Robotics Back-End](https://roboticsbackend.com/category/ros2/).

## Praticar (cerca de 5 horas)

Abra `infra/docker/ros.sh` e trabalhe em `/workspace`, para o código não sumir:

```bash
mkdir -p /workspace/ros2_ws/src && cd /workspace/ros2_ws/src
ros2 pkg create --build-type ament_python estudo --dependencies rclpy geometry_msgs turtlesim
cd .. && colcon build --symlink-install && source install/setup.bash
```

Com o `--symlink-install`, você edita o Python sem recompilar. Só recompile ao adicionar arquivos ou mudar o `setup.py`.

Exercícios, nesta ordem, cada um com a tartaruga rodando em outro terminal:

1. **Topic, leitura:** nó que assina `/turtle1/pose` e imprime só quando a tartaruga cruza `x > 8`.
2. **Topic, escrita:** nó que publica em `/turtle1/cmd_vel` e faz a tartaruga andar em círculo.
3. **Action:** nó com `ActionClient` que manda `RotateAbsolute`, imprime o feedback e, ao fim, o resultado.
4. **O desafio da semana:** junte os três. O nó gira a tartaruga por action, mas **cancela no meio se ela estiver com `x > 8`**. É o esqueleto da sua missão 1: agir, vigiar uma condição e cancelar.

## Pronto quando

O exercício 4 funciona e você sabe dizer em que linha cada callback é disparado e por que o programa não termina sozinho.

## Se travar

- `Package not found`: faltou `source install/setup.bash` neste terminal.
- Callback nunca dispara: falta `rclpy.spin(...)`, ou o nome do topic está errado. Confira com `ros2 topic list`.
- Mudou o `setup.py` e nada aconteceu: rode `colcon build` de novo.
- Arquivos com dono `root` no seu notebook: `infra/docker/ros.sh parar` devolve a pasta para o seu usuário.
