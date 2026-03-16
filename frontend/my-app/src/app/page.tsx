"use client";

import Link from "next/link";
import { Button, Column, Content, Grid, Heading, Stack } from "@carbon/react";
import { Settings } from "@carbon/icons-react";
import { useTranslation } from "react-i18next";

export default function Home() {
  const { t } = useTranslation();

  return (
    <Content className="home-layout">
      <Grid fullWidth className="home-layout__grid">
        <Column sm={4} md={6} lg={8} xlg={8} max={8}>
          <Stack gap={6}>
            <Heading>{t("home.title")}</Heading>
            <p className="cds--body-long-01">{t("home.subtitle")}</p>
          </Stack>
        </Column>
      </Grid>

      <div className="home-layout__settings">
        <Button
          as={Link}
          href="/settings"
          renderIcon={Settings}
          iconDescription="Settings"
          size="md"
          kind="primary"
        >
          {t("home.settings")}
        </Button>
      </div>
    </Content>
  );
}
