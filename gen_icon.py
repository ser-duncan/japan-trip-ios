#!/usr/bin/env python3
"""Generate torii gate app icons — dark navy + white sun, Myojin-style gate."""
import cairosvg

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <clipPath id="rrect">
      <rect width="512" height="512" rx="112" ry="112"/>
    </clipPath>
    <!-- Background radial rings -->
    <radialGradient id="bgRings" cx="50%" cy="52%" r="54%">
      <stop offset="0%"   stop-color="#232B5A"/>
      <stop offset="40%"  stop-color="#1C2348"/>
      <stop offset="100%" stop-color="#141932"/>
    </radialGradient>
    <!-- Subtle concentric ring glow -->
    <radialGradient id="ringGlow" cx="50%" cy="52%" r="50%">
      <stop offset="0%"  stop-color="#2A3470" stop-opacity="0"/>
      <stop offset="60%" stop-color="#2A3470" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#2A3470" stop-opacity="0"/>
    </radialGradient>
    <!-- Gate color -->
    <linearGradient id="gateGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="#C42020"/>
      <stop offset="100%" stop-color="#A01818"/>
    </linearGradient>
    <!-- Sun glow -->
    <radialGradient id="sunGlow" cx="50%" cy="50%" r="50%">
      <stop offset="70%"  stop-color="#FFFFFF"/>
      <stop offset="100%" stop-color="#DDEEFF" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <g clip-path="url(#rrect)">

    <!-- Background -->
    <rect width="512" height="512" fill="#161C3C"/>
    <rect width="512" height="512" fill="url(#bgRings)"/>

    <!-- Concentric decorative rings (subtle, like original) -->
    <circle cx="256" cy="268" r="195" fill="none" stroke="#252E62" stroke-width="22" opacity="0.7"/>
    <circle cx="256" cy="268" r="155" fill="none" stroke="#1E2754" stroke-width="16" opacity="0.6"/>
    <circle cx="256" cy="268" r="118" fill="none" stroke="#1B2349" stroke-width="12" opacity="0.5"/>

    <!-- Sun / white circle -->
    <circle cx="256" cy="268" r="96" fill="url(#sunGlow)"/>
    <circle cx="256" cy="268" r="90" fill="#FFFFFF"/>

    <!-- ===== MYOJIN TORII GATE ===== -->
    <!--
      Proportions tuned to match original icon's gate placement,
      but with authentic Myojin curved kasagi with upswept ends.

      Pillars: left cx=162, right cx=350, width=44
      Gate spans: ~x=115 to x=397
      Nuki (lower bar): y=270-292
      Shimaki (upper flat bar): y=196-214
      Kasagi (curved top beam): ~y=148-175 with ends sweeping up to ~y=130
    -->

    <!-- Left pillar -->
    <rect x="140" y="168" width="44" height="316" rx="5" fill="url(#gateGrad)"/>
    <!-- Right pillar -->
    <rect x="328" y="168" width="44" height="316" rx="5" fill="url(#gateGrad)"/>

    <!-- Nuki (lower crossbar) -->
    <rect x="116" y="272" width="280" height="24" rx="5" fill="url(#gateGrad)"/>
    <!-- Nuki end stubs past pillars -->
    <rect x="104" y="276" width="14" height="16" rx="3" fill="#A01818"/>
    <rect x="394" y="276" width="14" height="16" rx="3" fill="#A01818"/>

    <!-- Shimaki (upper flat beam, below kasagi) -->
    <rect x="108" y="196" width="296" height="22" rx="4" fill="url(#gateGrad)"/>

    <!-- Daiwa (pillar caps between shimaki and kasagi) -->
    <rect x="140" y="170" width="44" height="28" rx="3" fill="#A01818"/>
    <rect x="328" y="170" width="44" height="28" rx="3" fill="#A01818"/>

    <!--
      Kasagi — Myojin style:
      The beam curves gently downward in the center (sag) and
      sweeps UP at both ends. This is the distinctive Myojin shape.
    -->
    <!-- Main kasagi body (slightly curved — concave upward in centre) -->
    <path d="
      M 116 172
      C 116 172, 190 163, 256 165
      C 322 163, 396 172, 396 172
      L 396 190
      C 396 190, 322 181, 256 183
      C 190 181, 116 190, 116 190
      Z
    " fill="url(#gateGrad)"/>

    <!-- Left upswept wing tip -->
    <path d="
      M 116 172
      C  96 162,  82 150,  78 139
      C  75 131,  80 127,  88 132
      C  96 137, 106 150, 116 190
      Z
    " fill="#B81C1C"/>
    <!-- Left wing underside fill to join cleanly -->
    <path d="
      M 116 190
      C 106 150,  96 137,  88 132
      C  94 136, 102 148, 112 188
      Z
    " fill="#A01818"/>

    <!-- Right upswept wing tip -->
    <path d="
      M 396 172
      C 416 162, 430 150, 434 139
      C 437 131, 432 127, 424 132
      C 416 137, 406 150, 396 190
      Z
    " fill="#B81C1C"/>
    <!-- Right wing underside fill -->
    <path d="
      M 396 190
      C 406 150, 416 137, 424 132
      C 418 136, 410 148, 400 188
      Z
    " fill="#A01818"/>

  </g>
</svg>'''

with open('/home/user/japan-trip-ios/icon.svg', 'w') as f:
    f.write(SVG)

svg_bytes = SVG.encode('utf-8')

cairosvg.svg2png(bytestring=svg_bytes, write_to='/home/user/japan-trip-ios/www/icons/icon-512.png',
                 output_width=512, output_height=512)
cairosvg.svg2png(bytestring=svg_bytes, write_to='/home/user/japan-trip-ios/www/icons/icon-192.png',
                 output_width=192, output_height=192)

print("Done.")
