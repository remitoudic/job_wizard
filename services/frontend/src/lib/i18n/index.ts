import { addMessages, init, getLocaleFromNavigator } from 'svelte-i18n';

import en from './locales/en.json';
import fr from './locales/fr.json';
import de from './locales/de.json';

addMessages('en', en);
addMessages('fr', fr);
addMessages('de', de);

const SUPPORTED_LOCALES = ['en', 'fr', 'de'];

function resolveInitialLocale(): string {
	const navigatorLocale = getLocaleFromNavigator();
	if (!navigatorLocale) return 'en';

	// Extract the base language code (e.g. "en-US" -> "en", "fr-FR" -> "fr")
	const base = navigatorLocale.split('-')[0].toLowerCase();
	return SUPPORTED_LOCALES.includes(base) ? base : 'en';
}

init({
	fallbackLocale: 'en',
	initialLocale: resolveInitialLocale()
});
