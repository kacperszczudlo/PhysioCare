import { Stack, Link } from 'expo-router'
import { ScrollView, StyleSheet, Text, View } from 'react-native'

import { COOKIE_SECTIONS, PRIVACY_META, PRIVACY_SECTIONS } from '@/content/legalPrivacy'
import { colors, space, typography } from '@/theme/tokens'

type Doc = 'privacy' | 'cookies'

export function LegalDocumentScreen({ doc }: { doc: Doc }) {
  const sections = doc === 'privacy' ? PRIVACY_SECTIONS : COOKIE_SECTIONS
  const title = doc === 'privacy' ? PRIVACY_META.title : 'Polityka cookies'

  return (
    <View style={styles.root}>
      <Stack.Screen options={{ headerShown: true, title, presentation: 'card' }} />
      <ScrollView contentContainerStyle={styles.content}>
        {doc === 'privacy' ? (
          <Text style={styles.meta}>
            Wersja {PRIVACY_META.version} · Aktualizacja: {PRIVACY_META.updatedAt}
          </Text>
        ) : (
          <Text style={styles.meta}>Technologie w urządzeniu końcowym (PKE) — PhysioCare</Text>
        )}

        {sections.map((section) => (
          <View key={section.id} style={styles.section}>
            <Text style={styles.heading}>{section.title}</Text>
            {section.paragraphs.map((paragraph) => (
              <Text key={paragraph.slice(0, 40)} style={styles.paragraph}>
                {paragraph}
              </Text>
            ))}
          </View>
        ))}

        <View style={styles.links}>
          {doc === 'privacy' ? (
            <Link href="/legal/cookies" style={styles.link}>
              Polityka cookies
            </Link>
          ) : (
            <Link href="/legal/privacy" style={styles.link}>
              Polityka prywatności
            </Link>
          )}
          <Link href="/legal/account-deletion" style={styles.link}>
            Usuwanie konta
          </Link>
        </View>
      </ScrollView>
    </View>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  meta: { fontSize: typography.sm, color: colors.muted, marginBottom: space.sm },
  section: { gap: space.sm, marginBottom: space.md },
  heading: { fontSize: typography.lg, fontWeight: '700', color: colors.ink },
  paragraph: { fontSize: typography.sm, color: colors.ink, lineHeight: 22 },
  links: { gap: space.sm, marginTop: space.md },
  link: { color: colors.primary, fontWeight: '600', fontSize: typography.sm },
})
