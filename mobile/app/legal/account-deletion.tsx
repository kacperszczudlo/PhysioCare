import { Link } from 'expo-router'
import * as Linking from 'expo-linking'
import { Pressable, ScrollView, StyleSheet, Text } from 'react-native'

import { ACCOUNT_DELETION_MAILTO, DATA_CONTROLLER } from '@/content/dataController'
import { colors, space, typography } from '@/theme/tokens'

export default function AccountDeletionScreen() {
  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.content}>
      <Text style={styles.lede}>
        Możesz usunąć konto pacjenta z Ustawień albo złożyć wniosek poza aplikacją (wymóg Google
        Play / Apple).
      </Text>

      <Text style={styles.heading}>W aplikacji</Text>
      <Text style={styles.paragraph}>
        Ustawienia → „Wniosek o usunięcie konta” → wybierz powód i potwierdź. Konto zostaje
        wyłączone, dane osobowe zanonimizowane, a ten sam e-mail można ponownie zarejestrować. Dane
        medyczne mogą pozostać w systemie przez okres retencji wymagany prawem.
      </Text>

      <Text style={styles.heading}>Bez aplikacji</Text>
      <Text style={styles.paragraph}>
        Napisz do {DATA_CONTROLLER.name} (temat: „Usunięcie konta PhysioCare”). Podaj e-mail konta -
        nie wysyłaj hasła.
      </Text>
      <Pressable
        onPress={() => {
          void Linking.openURL(ACCOUNT_DELETION_MAILTO)
        }}
        accessibilityRole="link"
      >
        <Text style={styles.link}>{DATA_CONTROLLER.email}</Text>
      </Pressable>

      <Link href="/legal/privacy" style={styles.link}>
        Polityka prywatności
      </Link>
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.bg },
  content: { padding: space.lg, gap: space.base, paddingBottom: space['4xl'] },
  lede: { fontSize: typography.base, color: colors.ink, lineHeight: 24, marginBottom: space.sm },
  heading: { fontSize: typography.lg, fontWeight: '700', color: colors.ink, marginTop: space.sm },
  paragraph: { fontSize: typography.sm, color: colors.ink, lineHeight: 22 },
  link: { color: colors.primary, fontWeight: '600', fontSize: typography.sm, marginTop: space.sm },
})
