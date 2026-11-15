#!/usr/bin/env python3
"""Build the two public, one-page resumes from content/resumes.json + facts.json.
Requires reportlab. Historical work-sample transcriptions are maintained separately.
"""
import json
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from build import fill, problems, check_do_not_say
ROOT=Path(__file__).parent
font_dir=Path('/System/Library/Fonts/Supplemental')
for name, filename in [('PortfolioSans','Arial.ttf'),('PortfolioBold','Arial Bold.ttf'),('PortfolioSerif','Georgia Bold.ttf')]:
 pdfmetrics.registerFont(TTFont(name,str(font_dir/filename)))
ink=colors.HexColor('#1c1b19')
muted=colors.HexColor('#5f5b53')
styles={
 'name':ParagraphStyle('name',fontName='PortfolioSerif',fontSize=25,leading=29,textColor=ink,spaceAfter=4),
 'focus':ParagraphStyle('focus',fontName='PortfolioBold',fontSize=10.5,leading=13,textColor=ink,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='PortfolioSans',fontSize=9.1,leading=12,textColor=ink,spaceAfter=4),
 'small':ParagraphStyle('small',fontName='PortfolioSans',fontSize=8.5,leading=11,textColor=muted,spaceAfter=3),
 'section':ParagraphStyle('section',fontName='PortfolioBold',fontSize=10.5,leading=13,textColor=ink,spaceBefore=9,spaceAfter=5),
 'role':ParagraphStyle('role',fontName='PortfolioBold',fontSize=9.6,leading=12,textColor=ink),
 'date':ParagraphStyle('date',fontName='PortfolioSans',fontSize=8.6,leading=12,textColor=muted,alignment=2),
 'bullet':ParagraphStyle('bullet',fontName='PortfolioSans',fontSize=9.1,leading=12,textColor=ink,leftIndent=9,firstLineIndent=-7,spaceAfter=3),
}
def text(s):
 return escape(fill(s,'content/resumes.json')).replace('’',"'").replace('–','-')
def p(s,style='body'):
 return Paragraph(text(s), styles[style])
for cv in json.loads((ROOT/'content/resumes.json').read_text()):
 raw=json.dumps(cv,ensure_ascii=False)
 check_do_not_say(fill(raw,'content/resumes.json'),'content/resumes.json')
 if problems: raise ValueError('\n'.join(problems))
 out=ROOT/'assets'/f'Mathew-Godinez-{cv["name"]}.pdf'
 doc=SimpleDocTemplate(str(out),pagesize=letter,leftMargin=42,rightMargin=42,topMargin=34,bottomMargin=34,title=f'Mathew Godinez | {cv["focus"]}',author='Mathew Godinez')
 story=[p('Mathew Godinez','name'),p(cv['focus'],'focus')]
 story.append(Paragraph('Berkeley, CA | <link href="mailto:'+text('{{public_email}}')+'">'+text('{{public_email}}')+'</link><br/><link href="https://matthewgodinez24-boop.github.io/">matthewgodinez24-boop.github.io</link> | <link href="'+text('{{linkedin}}')+'">linkedin.com/in/mathew-godinez</link>',styles['small']))
 story.extend([Spacer(1,4),p(cv['summary']),p('Education','section'),p('University of California, Berkeley | B.A. Cognitive Science','role'),p('Expected {{graduation}} | Available {{available_from}}','small'),p('Experience','section')])
 for entry in cv['experience']:
  row=Table([[p(entry['title'],'role'),p(entry['dates'],'date')]],colWidths=[345,183])
  row.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),1),('VALIGN',(0,0),(-1,-1),'TOP')]))
  lines=[row,p(entry['subtitle'],'small')]+[p('• '+b,'bullet') for b in entry['bullets']]+[Spacer(1,5)]
  story.append(KeepTogether(lines))
 story.append(p('Leadership','section'))
 story.extend(p(s) for s in cv['leadership'])
 story.extend([p('Skills','section'),p(cv['skills'])])
 doc.build(story)
 print(out.name)
