"""Propagationsmaschine (2-Watch, mit Ruecknahme)."""
# ====================================================== Propagationsmaschine
class Prop:
    """Unit-Propagation mit zwei beobachteten Literalen, mit Ruecknahme."""
    def __init__(self, cls, n):
        self.n = n
        self.cls = [c for c in cls if len(c) > 1]
        self.units = [c[0] for c in cls if len(c) == 1]
        self.assign = [-1] * (n + 1)
        self.trail = []
        self.watch = {}
        for i, c in enumerate(self.cls):
            self.watch.setdefault(c[0], []).append(i)
            self.watch.setdefault(c[1], []).append(i)

    def val(self, l):
        a = self.assign[abs(l)]
        if a < 0: return -1
        return a if l > 0 else a ^ 1

    def enqueue(self, l):
        v = self.val(l)
        if v == 1: return True
        if v == 0: return False
        self.assign[abs(l)] = 1 if l > 0 else 0
        self.trail.append(l)
        return True

    def propagate(self, start):
        i = start
        while i < len(self.trail):
            l = self.trail[i]; i += 1
            wl = self.watch.get(-l)
            if not wl: continue
            rest = []
            for ci in wl:
                c = self.cls[ci]
                if c[0] == -l: c[0], c[1] = c[1], c[0]
                if self.val(c[0]) == 1:
                    rest.append(ci); continue
                for k in range(2, len(c)):
                    if self.val(c[k]) != 0:
                        c[1], c[k] = c[k], c[1]
                        self.watch.setdefault(c[1], []).append(ci)
                        break
                else:
                    rest.append(ci)
                    if not self.enqueue(c[0]):
                        self.watch[-l] = rest + wl[wl.index(ci)+1:]
                        return False
            self.watch[-l] = rest
        return True

    def start(self):
        for u in self.units:
            if not self.enqueue(u): return False
        return self.propagate(0)

    def mark(self): return len(self.trail)
    def undo(self, m):
        while len(self.trail) > m:
            self.assign[abs(self.trail.pop())] = -1

    def entschieden(self, l):
        m = self.mark()
        ok = self.enqueue(l) and self.propagate(m)
        return ok

    def offen(self):
        return sum(1 for v in range(1, self.n + 1) if self.assign[v] < 0)


