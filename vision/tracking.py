import math

FACE_POINTS = [0, 1, 2, 3, 4]     # Pose-punkter i ansiktet: nese, venstre/høyre øye, venstre/høyre øre
POINT_CONF = 0.5                  # Summen av sikkerheten til ansiktspunktene må være over dette, ellers brukes boksen

AIM_BELOW_CM = 30.0     # Sikter så mange cm under hodet
SHOULDER_CM = 40.0      # Omtrentlig skulderbredde på en voksen, brukes som målestokk for cm -> piksler
L_SHOULDER, R_SHOULDER = 5, 6     # Pose-punktene for venstre og høyre skulder


def find_target(result):
    """Finner ansiktet til personen YOLO er sikrest på. Gir (xt, yt) i piksler, eller None hvis ingen mål."""
    if len(result.boxes) == 0:
        return None

    # keypoints.xy[0] = (x, y) for de 17 punktene på den første personen, keypoints.conf[0] = hvor sikre de er
    points = result.keypoints.xy[0].tolist()
    confs = result.keypoints.conf[0].tolist() if result.keypoints.conf is not None else [0] * len(points)

    # 1. Vektet snitt av nese, øyne og ører: et punkt teller like mye som YOLO er sikker på det.
    # Ingen hard grense mellom "nese" og "øyne", så målet glir i stedet for å hoppe når nesa blir usikker
    total = sum(confs[i] for i in FACE_POINTS)
    if total > POINT_CONF:
        xt = sum(points[i][0] * confs[i] for i in FACE_POINTS) / total
        yt = sum(points[i][1] * confs[i] for i in FACE_POINTS) / total

        # Flytt målet AIM_BELOW_CM ned. Skulderbredden i piksler sier hvor mange piksler en cm er på denne avstanden.
        # Synes ikke begge skuldrene, siktes det rett på hodet
        if confs[L_SHOULDER] > POINT_CONF and confs[R_SHOULDER] > POINT_CONF:
            shoulder_px = math.dist(points[L_SHOULDER], points[R_SHOULDER])     # Avstand mellom skuldrene i piksler
            yt += AIM_BELOW_CM * shoulder_px / SHOULDER_CM     # y-aksen peker nedover, så + er ned
        return xt, yt

    # 2. Ellers øvre del av boksen, der hodet som regel er
    # xyxy = hjørnene på boksen: (x1, y1) øverst til venstre, (x2, y2) nederst til høyre
    x1, y1, x2, y2 = result.boxes.xyxy[0].tolist()
    xt = (x1 + x2) / 2              # Midt på i bredden
    yt = y1 + 0.15 * (y2 - y1)      # 15 % ned fra toppen av boksen
    return xt, yt


def system_error(xt, yt, width, height):
    """System error, ligning (1): e = bildets sentrum - målets posisjon. Gir (ex, ey) i piksler."""
    xc = width / 2          # Bildets sentrum langs x-aksen
    yc = height / 2         # Bildets sentrum langs y-aksen

    # ex > 0: målet er til venstre for sentrum. ey > 0: målet er over sentrum (y-aksen i bilder peker nedover).
    ex = xc - xt
    ey = yc - yt
    return ex, ey
