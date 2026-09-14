import React from 'react'
import { StyleSheet, View } from 'react-native'

import { colors, radius, space } from '@/theme/tokens'
import { Skeleton, SkeletonAvatar, SkeletonText, SkeletonWrapper } from '@/components/Skeleton'

export function MobileDashboardSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie pulpitu…" style={styles.container}>
      {/* Header */}
      <View style={styles.rowBetween}>
        <View style={styles.rowGap}>
          <SkeletonAvatar size={48} />
          <View style={{ gap: space.xs }}>
            <Skeleton width={140} height={18} />
            <Skeleton width={90} height={12} />
          </View>
        </View>
        <Skeleton width={36} height={36} circle />
      </View>

      {/* Stats Cards */}
      <View style={styles.rowGrid}>
        <View style={styles.cardHalf}>
          <Skeleton width={80} height={12} />
          <Skeleton width={50} height={26} style={{ marginTop: space.xs }} />
        </View>
        <View style={styles.cardHalf}>
          <Skeleton width={90} height={12} />
          <Skeleton width={50} height={26} style={{ marginTop: space.xs }} />
        </View>
      </View>

      {/* Highlight Visit Card */}
      <View style={styles.card}>
        <View style={styles.rowBetween}>
          <Skeleton width={110} height={14} />
          <Skeleton width={70} height={20} borderRadius={radius.sm} />
        </View>
        <View style={[styles.rowGap, { marginTop: space.md }]}>
          <SkeletonAvatar size={40} />
          <View style={{ gap: space.xs, flex: 1 }}>
            <Skeleton width="70%" height={16} />
            <Skeleton width="45%" height={12} />
          </View>
        </View>
        <Skeleton width="100%" height={40} borderRadius={radius.md} style={{ marginTop: space.md }} />
      </View>

      {/* Recent Activity / Exercises */}
      <View style={styles.card}>
        <Skeleton width={130} height={16} />
        <SkeletonText lines={3} gap={space.sm} style={{ marginTop: space.md }} />
      </View>
    </SkeletonWrapper>
  )
}

export function MobileVisitsSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie wizyt…" style={styles.container}>
      {/* Tabs */}
      <View style={styles.rowGrid}>
        <Skeleton width="30%" height={32} borderRadius={radius.md} />
        <Skeleton width="30%" height={32} borderRadius={radius.md} />
        <Skeleton width="30%" height={32} borderRadius={radius.md} />
      </View>

      {/* Visit Cards */}
      {Array.from({ length: 3 }).map((_, index) => (
        <View key={index} style={styles.card}>
          <View style={styles.rowBetween}>
            <Skeleton width={120} height={14} />
            <Skeleton width={64} height={20} borderRadius={radius.sm} />
          </View>
          <View style={[styles.rowGap, { marginTop: space.sm }]}>
            <SkeletonAvatar size={36} />
            <View style={{ gap: space.xs, flex: 1 }}>
              <Skeleton width="60%" height={15} />
              <Skeleton width="40%" height={12} />
            </View>
          </View>
        </View>
      ))}
    </SkeletonWrapper>
  )
}

export function MobileDocumentsSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie dokumentów…" style={styles.container}>
      <View style={styles.rowBetween}>
        <Skeleton width={150} height={22} />
        <Skeleton width={100} height={36} borderRadius={radius.md} />
      </View>

      {Array.from({ length: 4 }).map((_, index) => (
        <View key={index} style={styles.cardRow}>
          <Skeleton width={40} height={40} borderRadius={radius.md} />
          <View style={{ gap: space.xs, flex: 1 }}>
            <Skeleton width="75%" height={15} />
            <Skeleton width="45%" height={12} />
          </View>
          <Skeleton width={32} height={32} circle />
        </View>
      ))}
    </SkeletonWrapper>
  )
}

export function MobileProfileSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie profilu…" style={styles.container}>
      <View style={styles.centerCard}>
        <SkeletonAvatar size={72} />
        <Skeleton width={160} height={20} style={{ marginTop: space.sm }} />
        <Skeleton width={110} height={14} style={{ marginTop: space.xs }} />
      </View>

      <View style={styles.card}>
        <Skeleton width={130} height={16} />
        <SkeletonText lines={4} gap={space.md} style={{ marginTop: space.md }} />
      </View>
    </SkeletonWrapper>
  )
}

export function MobileVisitDetailSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie szczegółów wizyty…" style={styles.container}>
      <View style={styles.card}>
        <Skeleton width={120} height={24} borderRadius={radius.md} />
        <Skeleton width="80%" height={16} style={{ marginTop: space.sm }} />
      </View>

      <View style={styles.card}>
        <Skeleton width={140} height={16} />
        <SkeletonText lines={4} gap={space.md} style={{ marginTop: space.md }} />
      </View>
    </SkeletonWrapper>
  )
}

export function MobileExerciseDetailSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie szczegółów ćwiczenia…" style={styles.container}>
      <Skeleton width="100%" height={200} borderRadius={radius.lg} />
      <Skeleton width="70%" height={22} style={{ marginTop: space.md }} />
      <View style={[styles.rowGap, { marginTop: space.xs }]}>
        <Skeleton width={80} height={22} borderRadius={radius.sm} />
        <Skeleton width={60} height={22} borderRadius={radius.sm} />
      </View>
      <View style={[styles.card, { marginTop: space.md }]}>
        <Skeleton width={120} height={16} />
        <SkeletonText lines={4} gap={space.sm} style={{ marginTop: space.sm }} />
      </View>
    </SkeletonWrapper>
  )
}

const styles = StyleSheet.create({
  container: {
    gap: space.base,
    paddingVertical: space.base,
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rowGap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
  },
  rowGrid: {
    flexDirection: 'row',
    gap: space.md,
    justifyContent: 'space-between',
  },
  cardHalf: {
    flex: 1,
    padding: space.base,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  card: {
    padding: space.base,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: space.md,
    padding: space.base,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  centerCard: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: space.xl,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
})
