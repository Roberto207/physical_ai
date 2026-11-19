"""Apoio dos testes L0 do lab_tb4: põe o pacote no caminho, sem ROS."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
