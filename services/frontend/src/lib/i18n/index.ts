import { addMessages, init, getLocaleFromNavigator } from 'svelte-i18n';

import en from './locales/en.json';
import fr from './locales/fr.json';
import de from './locales/de.json';

addMessages('en', en);
addMessages('fr', fr);
addMessages('de', de);

init({
  fallbackLocale: 'en',
  initialLocale: getLocaleFromNavigator(),
});
