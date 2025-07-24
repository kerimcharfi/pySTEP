import math


class Gerade:

    def __init__(self, stutze, richtung):
        self.stutzvektor = stutze
        self.richtung = richtung

    def __eq__(self, other):
        if (isinstance(other, Gerade)):
            if other.richtung.isparallelto(self.richtung) and self.punktprobe(other.stutzvektor):
                return True
        return False

    def __str__(self):
        return "Gerade: " + "stützvektor: " + str(self.stutzvektor) + "richtungsvektor: " + str(self.richtung)

    def punktprobe(self, othervektor):
        zwischenergebnis = othervektor - self.stutzvektor
        if not math.isclose(self.richtung.koordinaten[0], 0, abs_tol=1e-12):
            first_t = zwischenergebnis.koordinaten[0] / self.richtung.koordinaten[0]
        else:
            first_t = 0
        for i in range(0, len(self.stutzvektor)):
            if not math.isclose(self.richtung.koordinaten[i], 0, abs_tol=1e-12):
                if not math.isclose(first_t, zwischenergebnis.koordinaten[i] / self.richtung.koordinaten[i], rel_tol=1e-8):
                    return False
            elif not math.isclose(zwischenergebnis.koordinaten[i], 0, abs_tol=1e-12):
                return False
        return True

    def is_parallel(self, othergerade):
        if self.richtung.isparallelto(othergerade.richtung):
            return True
        return False

    def rotate_around_axis(self, axis, angle):
        self.stutzvektor.rotate_around_axis(axis, angle)
        self.richtung.rotate_around_axis(axis, angle)

    def translate(self, u):
        self.stutzvektor.translate(u)


class Ebene:
    def __init__(self, sv, nv):
        self.sv = sv
        self.nv = nv.norm()

    def schnittpunktGerade(self, gerade: Gerade):
        langederprojektion = self.nv * gerade.richtung
        faktor = self.distancepoint(gerade.stutzvektor) / langederprojektion
        return gerade.richtung * faktor + gerade.stutzvektor

    def distancepoint(self, otherpoint):
        verbindung = otherpoint - self.sv
        distance = abs(verbindung * self.nv)
        return distance

    def distanceebene(self, otherebene):
        return self.distancepoint(otherebene.sv)
