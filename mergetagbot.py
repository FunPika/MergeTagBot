# Checks if a merge template's target has another merge template linking back.
# Licensed under the MIT License.
from pywikibot import catlib
from pywikibot import pagegenerators
import pywikibot
site = pywikibot.getSite()
cat = catlib.Category(site,'Category:All articles to be merged')
gen = pagegenerators.CategorizedPageGenerator(cat)
print('Starting bot run...')
for page in gen:
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
			for param in params:
				date = ''
				discuss = ''
				section = ''
				if param.startswith('date='): # If a new tag needs to be added, preserve the date and discuss parameters.
					date = '|' + param
				elif param.startswith('discuss='):
					discuss = '|' + param
				if not (param.find('=') != -1 and param.find('{{=}}') == -1): # If a non-escaped = is in the parameter, assume it is named.
					targetpage = pywikibot.Page(site, param.replace('{{=}}', '='))
					if targetpage.isRedirectPage(): # If the target page is a redirect, resolve it
						targetpage = targetpage.getRedirectTarget()
					print('Checking for link back on page ' + targetpage.title())
					targettemplates = targetpage.templatesWithParams()
					foundlinkback = 0
					templatecount = 0
					for targettemplate, targetparams in targettemplates:
						targettemplate_cap = targettemplate.title(withNamespace=False).replace(' ', '').capitalize()
						if targettemplate_cap == othertemplate:
							templatecount += 1
							for targetparam in targetparams:
								if not (param.find('=') != -1 and param.find('{{=}}') == -1): # If a non-escaped = is in the parameter, assume it is named.
									targetpage2 = pywikibot.Page(site, targetparam.replace('{{=}}', '='))
									if targetpage2.isRedirectPage():
										targetpage2 = targetpage2.getRedirectTarget()
									if targetpage2.title() == page.title():
										foundlinkback = 1
					if templatecount == 0: # If there is no merge template on the target page, one needs to be added.
						print('No {{' + othertemplate + '}} template found on target page')
						tagtext = '{{' + othertemplate + '|' + page.title() + date + discuss + '}}'
						page.text() = tagtext + page.text()
						page.save('BOT: Add merge tag due to [[' + page.title() + ']] having a merge tag pointing here. If there is no consensus to merge, remove both merge templates.')
					elif foundlinkback == 1: # If a link to the first page is found, no action is required.
						print('Found link back to first page, no edit is needed.')
					elif templatecount > 0: # If existing merge templates are found, log it so a human can decide on how to proceed.
						print('Multiple merge templates found! Logging to [[User:FPBot/Merge problem log]]...')
						logtext = '* Existing merge tag(s) found on [[' + targetpage.title() + ']] that do not link back to [[' + page.title() + ']].\n'
print('Bot run complete!')
