# Checks if a merge template's target has another merge template linking back.
# Licensed under the MIT License.

from pywikibot import catlib
from pywikibot import pagegenerators
import pywikibot
import re

pywikibot.simulate = True # Just to be safe for now...

pagecount = 0
taggedcount = 0
loggedcount = 0
tagsremoved = 0
tagschanged = 0

def removemergetemplate(page, templatetoremove):
	global tagsremoved, loggedcount
	templatecount = 0
	templates = page.templatesWithParams()
	for template, params in templates:
		template_cap = template.title(withNamespace=False).replace(' ', '').capitalize()
		if (template_cap == templatetoremove):
			templatecount += 1
			templateregtext = template.title(withNamespace=False)
	if not templatecount == 1:
		print('Unable to remove merge template, a number of merge templates other than 1 has been found')
		loggedcount += 1
		return
	else: # Remove the template if only one has been found.
		templateregex = re.compile('\{\{' + templateregtext + '\|.*\}\}', re.IGNORECASE)
		newpagetext = templateregex.sub('', page.text)
		pywikibot.showDiff(page.text, newpagetext)
		page.text = newpagetext
		page.save('BOT: Removing merge tag with invalid or non-existant target pages.')
		tagsremoved += 1
	return

site = pywikibot.getSite()
logpage_title = 'User:FPBot/Merge problem log'
logpage = pywikibot.Page(site, logpage_title)
cat = catlib.Category(site, 'Category:All articles to be merged') # TODO: Add parameter for it to use this category, but default to previous month's category.
gen = pagegenerators.CategorizedPageGenerator(cat)
print('Starting bot run...')

for page in gen:
	pagecount += 1
	print('Opening page ' + page.title())
	templates = page.templatesWithParams()
	for template, params in templates:
		template_cap = template.title(withNamespace=False).replace(' ', '').capitalize()
		if (template_cap == 'Merge' or template_cap == 'Mergeto' or template_cap == 'Mergefrom'):
			print('Found {{' + template_cap + '}} template')
			if template_cap == 'Merge': # Determine the name of what the template used on the linked page should be.
				othertemplate = 'Merge'
			elif template_cap == 'Mergeto':
				othertemplate = 'Mergefrom'
			elif template_cap == 'Mergefrom':
				othertemplate = 'Mergeto'
			linksthatexist = 0
			selflinks = 0
			date = ''
			discuss = ''
			
			for param in params:
				if not param: # Skip this parameter if its empty.
					continue
				
				target = ''
				if param.startswith('date='): # If a new tag needs to be added, preserve the date and discuss parameters.
					date = '|' + param
					continue
				elif param.startswith('discuss='):
					discuss = '|' + param
					continue
				elif param.startswith('target=') and template_cap == 'Merge':
					target = param.replace('target=', '')
				else:
					target = param
				
				target = target.replace('{{=}}', '=')
				targetpage = pywikibot.Page(site, target)
				if targetpage.isRedirectPage(): # If the target page is a redirect, follow it
					targetpage = targetpage.getRedirectTarget()
				if targetpage.exists():
					linksthatexist += 1
				else:
					continue
				if targetpage.title() == page.title(): # If the merge template links to itself, note this but continue checking other params.
					selflinks += 1
					continue
				
				print('Checking for link back on page ' + targetpage.title())
				targettemplates = targetpage.templatesWithParams()
				foundlinkback = 0
				templatecount = 0
				
				for targettemplate, targetparams in targettemplates:
					targettemplate_cap = targettemplate.title(withNamespace=False).replace(' ', '').capitalize()
					if not (targettemplate_cap == othertemplate):
						continue
					templateregtext = targettemplate.title(withNamespace=False)
					templatecount += 1
					for targetparam in targetparams:
						targetpage2 = pywikibot.Page(site, targetparam.replace('{{=}}', '='))
						if targetpage2.isRedirectPage():
							targetpage2 = targetpage2.getRedirectTarget()
						if targetpage2.title() == page.title():
							foundlinkback = 1
				
				if foundlinkback == 1:
					print('Found link back to first page, no edit is needed.')
					continue
				if templatecount == 0: # If there is no merge template on the target page, one needs to be added.
					print('No {{' + othertemplate + '}} template found on target page')
					tagtext = '{{' + othertemplate + '|' + page.title() + date + discuss + '}}'
					targetpage.text = tagtext + page.text
					targetpage.save('BOT: Add merge tag due to [[' + page.title() + ']] having a merge tag pointing here. If there is no consensus to merge, remove both merge templates.')
					taggedcount += 1
				elif templatecount == 1: # If a single existing merge template exists, add the source page as a parameter.
					print('Single existing merge template found. Adding page we came from as a parameter.')
					templateregex = re.compile('\{\{' + templateregtext + '\|.*\}\}', re.IGNORECASE)
					templatematch = templateregex.match(targetpage.text)
					existingtemplate = templatematch.group(0)
					newtemplate = existingtemplate[:-2] + '|' + page.title() + '}}'
					newtext = templateregex.sub(newtemplate, targetpage.text)
					pywikibot.showDiff(targetpage.text, newtext)
					targetpage.text = newtext
					targetpage.save('BOT: Adding [[' + page.title() + ']] to existing merge template. If there is no consensus to merge, remove both merge templates')
					tagschanged += 1
				elif templatecount > 1: # If existing merge templates are found, log it so a human can decide on how to proceed.
					print('Multiple existing merge templates found! Logging to [[' + logpage_title + ']]...')
					logtext = '* Multiple existing merge templates found on [[' + targetpage.title() + ']] that do not link back to [[' + page.title() + ']].\n'
					logpage.text = logtext + logpage.text
					logpage.save('BOT: Logging issue with merge tags that needs human attention.')
					loggedcount += 1
			
			if linksthatexist == 0:
				print('No target pages found! Removing the merge template!')
				removemergetemplate(page, template_cap)
			elif selflinks == linksthatexist:
				print('Only target page is the source page! Removing the merge template!')
				removemergetemplate(page, template_cap)
	if ((pagecount % 10) == 0):
		print('\033[95m' + str(pagecount) + ' pages processed, ' + str(taggedcount) + ' pages tagged, ' + str(tagsremoved) + ' tags removed, ' + str(tagschanged) + ' tags changed, ' + str(loggedcount) + ' pages logged.\033[0m')

print('Bot run complete!')
