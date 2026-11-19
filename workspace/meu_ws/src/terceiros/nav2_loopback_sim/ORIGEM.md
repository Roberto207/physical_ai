# Origem deste pacote (vendorizado)

| Campo | Valor |
|---|---|
| Upstream | https://github.com/ros-navigation/navigation2, pasta `nav2_loopback_sim/` |
| Ramo | `jazzy` |
| Commit copiado | `c7046550547d382a5186d106b0895eda02485d7c` |
| Versão no `package.xml` | 1.3.14 |
| Data da cópia | 2026-11-18 |
| Licença | Apache-2.0 (`LICENSE` da raiz do navigation2, copiado aqui) |

## Por que está aqui

O `nav2_loopback_sim` não tem release para o ROS 2 Humble (index.ros.org, conferido em 2026-11-18): ele só existe do Jazzy em diante. O L1 da patrulha (os 11 cenários de `infra/docker/teste_l1.sh`) depende dele. Decisão: `docs/decisoes/ADR-002-gazebo-principal-no-pc-do-lab.md`. Requisito: SIM-07 de `specs/migracao-humble/DEFINE.md`.

## Patches aplicados

**Nenhum.** O código foi copiado sem mudança, porque já funciona com o que o Humble oferece:

- `nav2_simple_commander.line_iterator.LineIterator(x0, y0, x1, y1, step_size)`, com `isValid`, `getX`, `getY` e `advance`: existe no `nav2_simple_commander` do Humble (lido no ramo `humble` em 2026-11-18).
- `enable_stamped_cmd_vel` já tem padrão `False`: assina `geometry_msgs/Twist`, que é o que o Nav2 Humble publica.
- `tf_transformations` e `transforms3d`: instalados na imagem `physical-ai:sim` (`ros-humble-tf-transformations`, `python3-transforms3d`).

Os parâmetros de frame do TurtleBot 4 (`base_frame_id`, `scan_frame_id` e o resto) são passados pelo nosso `lab_tb4/launch/sim_leve.launch.py`, e não por patch aqui.

## Como conferir que não mudou nada

```bash
git clone --depth 1 --filter=blob:none --sparse -b jazzy https://github.com/ros-navigation/navigation2 /tmp/nav2
cd /tmp/nav2 && git checkout c7046550547d382a5186d106b0895eda02485d7c && git sparse-checkout set nav2_loopback_sim
diff -r /tmp/nav2/nav2_loopback_sim <esta pasta>   # só LICENSE e ORIGEM.md a mais
```

Não edite os arquivos do upstream. Se for preciso um patch, registre aqui o arquivo, a linha e o motivo.
