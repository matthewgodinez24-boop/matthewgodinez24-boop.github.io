#!/usr/bin/env python3
"""Render the simple typographic sharing image. Requires Pillow and local Georgia/Arial fonts."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).parent
fonts=Path('/System/Library/Fonts/Supplemental')
canvas=Image.new('RGB',(1200,630),'#fbfaf7')
draw=ImageDraw.Draw(canvas)
draw.text((78,112),'Mathew Godinez',font=ImageFont.truetype(str(fonts/'Georgia.ttf'),76),fill='#1c1b19')
draw.text((82,234),'Growth & go-to-market',font=ImageFont.truetype(str(fonts/'Arial.ttf'),39),fill='#0d5c4b')
draw.line((82,324,1118,324),fill='#e3dfd6',width=2)
draw.text((82,375),'ReLease  ·  Outreach workflows  ·  Reqest',font=ImageFont.truetype(str(fonts/'Arial.ttf'),32),fill='#1c1b19')
draw.text((82,500),'Selected work by a UC Berkeley student founder',font=ImageFont.truetype(str(fonts/'Arial.ttf'),26),fill='#5f5b53')
canvas.save(ROOT/'assets/social-preview.png',optimize=True)
