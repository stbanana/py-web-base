'use client';

import Link from 'next/link';
import {
  Button,
  Content,
  Heading,
  RadioButton,
  RadioButtonGroup,
  Stack,
  Tile,
} from '@carbon/react';
import { ArrowLeft } from '@carbon/icons-react';
import { useAppTheme } from '@/components/theme-provider';
import { useTranslation } from 'react-i18next';
import i18n, { supportedLanguages } from '@/i18n';

export default function SettingsPage() {
  const { theme, setTheme } = useAppTheme();
  const { t } = useTranslation();

  const currentLang = i18n.language;
  const handleLangChange = (selection: string | number | undefined) => {
    if (typeof selection === 'string') {
      i18n.changeLanguage(selection);
    }
  };

  return (
    <Content className="settings-page">
      <Stack gap={7}>
        <div className="settings-page__header">
          <Button
            as={Link}
            href="/"
            className="settings-page__back-link"
            renderIcon={ArrowLeft}
            iconDescription="Back"
            kind="ghost"
            size="sm"
          >
            {t('settings.back')}
          </Button>
          <Heading className="settings-page__title">{t('settings.title')}</Heading>
        </div>

        <Tile className="settings-page__tile">
          <Heading className="settings-page__section-title">{t('settings.theme')}</Heading>
          <RadioButtonGroup
            legendText={t('settings.themeLegend')}
            name="theme"
            valueSelected={theme}
            onChange={(value) => setTheme(value as 'white' | 'g90')}
          >
            <RadioButton id="theme-white" labelText={t('settings.themeWhite')} value="white" />
            <RadioButton id="theme-g90" labelText={t('settings.themeG90')} value="g90" />
          </RadioButtonGroup>
        </Tile>

        <Tile className="settings-page__tile">
          <Heading className="settings-page__section-title">{t('settings.language', '语言')}</Heading>
          <RadioButtonGroup
            legendText={t('settings.languageLegend', '选择语言')}
            name="language"
            valueSelected={currentLang}
            onChange={handleLangChange}
          >
            <RadioButton id="lang-zh" labelText="简体中文" value="zh-CN" />
            <RadioButton id="lang-en" labelText="English" value="en-US" />
          </RadioButtonGroup>
        </Tile>
      </Stack>
    </Content>
  );
}
