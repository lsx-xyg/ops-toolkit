"""日志总线：线程安全，GUI/CLI 均可消费。"""
import queue


class LogBus:
    def __init__(self):
        self._q = queue.Queue()

    def log(self, msg):
        self._q.put(msg)

    def done(self):
        self._q.put("__DONE__")

    def drain(self):
        msgs = []
        done = False
        try:
            while True:
                m = self._q.get_nowait()
                if m == "__DONE__":
                    done = True
                else:
                    msgs.append(m)
        except queue.Empty:
            pass
        return msgs, done
