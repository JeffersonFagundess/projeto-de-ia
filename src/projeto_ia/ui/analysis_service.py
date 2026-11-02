"""Processo persistente que isola a busca da thread gráfica do Tkinter."""

import multiprocessing as mp
import os
import queue
import random


def _executar(entrada, saida, geracao):
    """Mantém modelo e caches aquecidos entre turnos no processo da IA."""
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")

    from projeto_ia.damas.assistant import analisar_turno

    while True:
        trabalho = entrada.get()
        if trabalho is None:
            return
        identificador, parametros = trabalho
        if identificador != geracao.value:
            continue

        def cancelado(id_trabalho=identificador):
            return id_trabalho != geracao.value

        def progresso(dados, id_trabalho=identificador):
            if cancelado():
                return
            try:
                saida.put_nowait((id_trabalho, "progresso", dados))
            except queue.Full:
                pass

        try:
            resposta = analisar_turno(
                parametros["estado"],
                com_ajuda=parametros["com_ajuda"],
                historico=parametros["historico"],
                sem_progresso=parametros["sem_progresso"],
                cancelado=cancelado,
                gerador=random.Random(parametros["semente"]),
                segundos=parametros["segundos"],
                profundidade_maxima=parametros["profundidade_maxima"],
                variar=parametros["variar"],
                progresso=progresso,
            )
            if not cancelado():
                saida.put((identificador, "resultado", resposta))
        except Exception as erro:  # noqa: BLE001 - fronteira do processo
            if not cancelado():
                saida.put((identificador, "erro", (type(erro).__name__, str(erro))))


class ServicoAnalise:
    """Fila não bloqueante para uma única IA persistente e cancelável."""

    def __init__(self):
        contexto = mp.get_context("spawn")
        self._entrada = contexto.Queue(maxsize=3)
        self._saida = contexto.Queue(maxsize=128)
        self._geracao = contexto.Value("Q", 0, lock=False)
        self._processo = contexto.Process(
            target=_executar,
            args=(self._entrada, self._saida, self._geracao),
            name="IA-Damas",
            daemon=True,
        )
        self._processo.start()

    @property
    def ativo(self):
        return self._processo.is_alive()

    def cancelar(self):
        self._geracao.value += 1
        return self._geracao.value

    def analisar(self, estado, com_ajuda, semente, historico, sem_progresso,
                 segundos=None, profundidade_maxima=12, variar=True):
        identificador = self.cancelar()
        parametros = {
            "estado": estado,
            "com_ajuda": com_ajuda,
            "semente": semente,
            "historico": historico,
            "sem_progresso": sem_progresso,
            "segundos": segundos,
            "profundidade_maxima": profundidade_maxima,
            "variar": variar,
        }
        while True:
            try:
                self._entrada.put_nowait((identificador, parametros))
                return identificador
            except queue.Full:
                try:
                    self._entrada.get_nowait()
                except queue.Empty:
                    continue

    def receber(self):
        eventos = []
        while True:
            try:
                eventos.append(self._saida.get_nowait())
            except queue.Empty:
                return eventos

    def fechar(self):
        self.cancelar()
        try:
            self._entrada.put_nowait(None)
        except queue.Full:
            try:
                self._entrada.get_nowait()
            except queue.Empty:
                pass
            self._entrada.put_nowait(None)
        self._processo.join(timeout=.3)
        if self._processo.is_alive():
            self._processo.terminate()
            self._processo.join(timeout=.3)
