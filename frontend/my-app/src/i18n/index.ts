import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { en } from "@/locales/en";
import { zh } from "@/locales/zh";

const STORAGE_KEY = "app-language";
const defaultLanguage = "zh-CN";
const supportedLanguages = ["zh-CN", "en-US"] as const;

type SupportedLanguage = (typeof supportedLanguages)[number];

function isSupportedLanguage(value: string): value is SupportedLanguage {
  return supportedLanguages.includes(value as SupportedLanguage);
}

function detectInitialLanguage(): SupportedLanguage {
  if (typeof window === "undefined") {
    return defaultLanguage;
  }

  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored && isSupportedLanguage(stored)) {
    return stored;
  }

  const browserLanguage = window.navigator.language;
  if (browserLanguage && isSupportedLanguage(browserLanguage)) {
    return browserLanguage;
  }

  if (browserLanguage?.toLowerCase().startsWith("zh")) {
    return "zh-CN";
  }

  return defaultLanguage;
}

if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    lng: detectInitialLanguage(),
    fallbackLng: defaultLanguage,
    supportedLngs: [...supportedLanguages],
    interpolation: {
      escapeValue: false,
    },
    resources: {
      "zh-CN": {
        common: zh,
      },
      "en-US": {
        common: en,
      },
    },
    defaultNS: "common",
  });
}

if (typeof window !== "undefined") {
  i18n.on("languageChanged", (language: string) => {
    window.localStorage.setItem(STORAGE_KEY, language);
    document.documentElement.lang = language;
  });
}

export { defaultLanguage, supportedLanguages, STORAGE_KEY };
export default i18n;
