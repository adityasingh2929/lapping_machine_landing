from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
p=Path(__file__).parent
out=Image.new('RGB',(1440,386),'#e9ecef');d=ImageDraw.Draw(out)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
for i,(name,label) in enumerate([('uno','1 · Existing position — left panel'),('tres','3 · Rear panel — right of column'),('quatro','4 · Opposite panel — between louvers')]):
 im=Image.open(p/f'cabinet_badge_{name}.png').convert('RGB');out.paste(im,(i*480,36));d.text((i*480+12,10),label,font=font,fill='#20262d')
out.save(p/'cabinet_nameplates_sheet.jpg',quality=91)
