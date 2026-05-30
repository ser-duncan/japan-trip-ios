#!/usr/bin/env python3
"""Generate torii gate icon matching the reference illustration."""
import cairosvg

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <clipPath id="clip">
      <rect width="512" height="512" rx="112" ry="112"/>
    </clipPath>

    <!-- Background: very dark navy, slightly lighter in centre -->
    <radialGradient id="bg" cx="50%" cy="54%" r="62%">
      <stop offset="0%"   stop-color="#1C2652"/>
      <stop offset="50%"  stop-color="#101840"/>
      <stop offset="100%" stop-color="#060A1A"/>
    </radialGradient>

    <!-- Moon: hard white circle with soft outer halo -->
    <radialGradient id="moon" cx="50%" cy="50%" r="50%">
      <stop offset="58%"  stop-color="#FFFFFF" stop-opacity="1"/>
      <stop offset="72%"  stop-color="#FFFFFF" stop-opacity="0.38"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>

    <!-- Pillar: side-lit cylinder feel, left=shadow, 20-25%=highlight, right=shadow -->
    <linearGradient id="pillar" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#B52E00"/>
      <stop offset="22%"  stop-color="#FF5828"/>
      <stop offset="55%"  stop-color="#E54010"/>
      <stop offset="100%" stop-color="#A52800"/>
    </linearGradient>

    <!-- Beam front face: bright top, slightly darker base -->
    <linearGradient id="beamFace" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#FF5828"/>
      <stop offset="35%"  stop-color="#E84010"/>
      <stop offset="100%" stop-color="#CC3800"/>
    </linearGradient>

    <!-- Kasagi top dark cap -->
    <linearGradient id="cap" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#0C1124"/>
      <stop offset="100%" stop-color="#182040"/>
    </linearGradient>

    <!-- Pillar band (dark ring accent) -->
    <linearGradient id="band" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#0A0F22"/>
      <stop offset="40%"  stop-color="#1A2245"/>
      <stop offset="100%" stop-color="#0A0F22"/>
    </linearGradient>
  </defs>

  <g clip-path="url(#clip)">

    <!-- ── Background ── -->
    <rect width="512" height="512" fill="url(#bg)"/>

    <!-- ── Moon halo layers ── -->
    <circle cx="256" cy="296" r="228" fill="#FFFFFF" opacity="0.035"/>
    <circle cx="256" cy="296" r="205" fill="#FFFFFF" opacity="0.045"/>
    <!-- Moon disc -->
    <circle cx="256" cy="296" r="180" fill="url(#moon)"/>

    <!-- ── GATE ── -->
    <!--
      Layout (all x symmetric about 256):
        Left pillar:   x=140–192  (52 px wide)
        Right pillar:  x=320–372  (52 px wide)
        Pillar height: y=188–500
        Shimaki:       y=224–262
        Nuki:          y=376–414
        Kasagi body:   y=178–228  (front face, curves up at ends)
        Kasagi cap:    y=158–182  (dark top face)
    -->

    <!-- Left pillar -->
    <rect x="140" y="188" width="52" height="316" fill="url(#pillar)"/>
    <!-- Right pillar -->
    <rect x="320" y="188" width="52" height="316" fill="url(#pillar)"/>

    <!-- Pillar dark bands (pair of rings mid-pillar) -->
    <rect x="135" y="364" width="62" height="10" rx="2" fill="url(#band)"/>
    <rect x="135" y="377" width="62" height="10" rx="2" fill="url(#band)"/>
    <rect x="315" y="364" width="62" height="10" rx="2" fill="url(#band)"/>
    <rect x="315" y="377" width="62" height="10" rx="2" fill="url(#band)"/>

    <!-- ── Nuki (lower crossbar) ── -->
    <!-- Dark top face of nuki -->
    <rect x="118" y="376" width="276" height="10" rx="1" fill="url(#cap)"/>
    <!-- Red front face -->
    <rect x="118" y="386" width="276" height="28" rx="3" fill="url(#beamFace)"/>
    <!-- Nuki kibana tabs (outside of pillars) -->
    <rect x="100" y="381" width="42" height="25" rx="3" fill="#E84010"/>
    <rect x="370" y="381" width="42" height="25" rx="3" fill="#E84010"/>
    <!-- Kibana dark top face -->
    <rect x="100" y="381" width="42" height="8"  rx="1" fill="url(#cap)"/>
    <rect x="370" y="381" width="42" height="8"  rx="1" fill="url(#cap)"/>

    <!-- ── Shimaki (upper flat beam) ── -->
    <!-- Dark top face -->
    <rect x="106" y="224" width="300" height="12" rx="1" fill="url(#cap)"/>
    <!-- Red front face -->
    <rect x="106" y="236" width="300" height="26" rx="3" fill="url(#beamFace)"/>
    <!-- Shimaki kibana tabs -->
    <rect x="86"  y="228" width="56" height="26" rx="3" fill="#E84010"/>
    <rect x="370" y="228" width="56" height="26" rx="3" fill="#E84010"/>
    <!-- Kibana dark top face -->
    <rect x="86"  y="228" width="56" height="10" rx="1" fill="url(#cap)"/>
    <rect x="370" y="228" width="56" height="10" rx="1" fill="url(#cap)"/>

    <!-- ── Kasagi front (red body, curves up at ends) ── -->
    <!--
      Main curved body: gently concave at centre (sags ~8 px), sweeps up at wings.
      Front face.
    -->
    <path d="
      M  88 192
      C  88 192, 170 176, 256 178
      C 342 176, 424 192, 424 192
      L 424 228
      C 424 228, 342 214, 256 216
      C 170 214,  88 228,  88 228
      Z
    " fill="url(#beamFace)"/>

    <!-- Left upswept wing -->
    <path d="
      M  88 192
      C  68 180,  54 163,  50 148
      C  48 138,  55 135,  65 142
      C  75 149,  84 166,  88 228
      Z
    " fill="#D63A0C"/>
    <!-- Right upswept wing -->
    <path d="
      M 424 192
      C 444 180, 458 163, 462 148
      C 464 138, 457 135, 447 142
      C 437 149, 428 166, 424 228
      Z
    " fill="#D63A0C"/>

    <!-- ── Kasagi dark top cap ── -->
    <!--
      Sits above the red body. This is the charcoal-coloured top surface
      giving the 3-D "beam viewed from slightly above" look.
    -->
    <path d="
      M  84 172
      C  84 172, 168 155, 256 157
      C 344 155, 428 172, 428 172
      L 428 194
      C 428 194, 344 178, 256 180
      C 168 178,  84 194,  84 194
      Z
    " fill="url(#cap)"/>

    <!-- Left cap wing -->
    <path d="
      M  84 172
      C  63 159,  49 141,  44 124
      C  42 114,  50 112,  61 119
      C  72 126,  81 145,  84 194
      Z
    " fill="#0C1124"/>
    <!-- Right cap wing -->
    <path d="
      M 428 172
      C 449 159, 463 141, 468 124
      C 470 114, 462 112, 451 119
      C 440 126, 431 145, 428 194
      Z
    " fill="#0C1124"/>

    <!-- Subtle highlight rim at base of dark cap (where cap meets red face) -->
    <path d="
      M  84 194  C  84 194, 168 178, 256 180  C 344 178, 428 194, 428 194
      L 428 196  C 428 196, 344 181, 256 183  C 168 181,  84 196,  84 196
      Z
    " fill="#FF6030" opacity="0.6"/>

  </g>
</svg>'''

with open('/home/user/japan-trip-ios/icon.svg', 'w') as f:
    f.write(SVG)

svg_bytes = SVG.encode('utf-8')

cairosvg.svg2png(bytestring=svg_bytes,
                 write_to='/home/user/japan-trip-ios/www/icons/icon-512.png',
                 output_width=512, output_height=512)
cairosvg.svg2png(bytestring=svg_bytes,
                 write_to='/home/user/japan-trip-ios/www/icons/icon-192.png',
                 output_width=192, output_height=192)

print("Done.")
