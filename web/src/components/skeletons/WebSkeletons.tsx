import { Skeleton, SkeletonAvatar, SkeletonText, SkeletonWrapper } from '@/components/ui/Skeleton'
import './WebSkeletons.css'

export function DashboardSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie pulpitu…" className="skeleton-dashboard">
      <div className="skeleton-dash-header">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
          <Skeleton width="40%" height="2rem" radius="md" />
          <Skeleton width="25%" height="1rem" radius="sm" />
        </div>
        <Skeleton width="7rem" height="3.5rem" radius="md" />
      </div>

      <div className="skeleton-dash-metrics">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="skeleton-dash-metric-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Skeleton width="50%" height="1rem" radius="sm" />
              <Skeleton circle width="2rem" height="2rem" />
            </div>
            <Skeleton width="35%" height="2.25rem" radius="md" />
            <Skeleton width="60%" height="0.875rem" radius="sm" />
          </div>
        ))}
      </div>

      <div className="skeleton-dash-grid">
        <div className="skeleton-panel">
          <Skeleton width="30%" height="1.5rem" radius="sm" />
          <div
            style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '0.5rem' }}
          >
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="skeleton-list-row">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1 }}>
                  <SkeletonAvatar size="md" />
                  <div
                    style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1 }}
                  >
                    <Skeleton width="45%" height="1rem" radius="sm" />
                    <Skeleton width="30%" height="0.8rem" radius="sm" />
                  </div>
                </div>
                <Skeleton width="5rem" height="1.75rem" radius="md" />
              </div>
            ))}
          </div>
        </div>

        <div className="skeleton-panel">
          <Skeleton width="50%" height="1.5rem" radius="sm" />
          <SkeletonText lines={4} gap="0.75rem" />
          <Skeleton width="100%" height="2.5rem" radius="md" style={{ marginTop: '0.5rem' }} />
        </div>
      </div>
    </SkeletonWrapper>
  )
}

export function PatientsSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie listy pacjentów…" className="skeleton-dashboard">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          gap: '1rem',
          marginBottom: '1rem',
        }}
      >
        <Skeleton width="60%" height="2.5rem" radius="md" />
        <Skeleton width="20%" height="2.5rem" radius="md" />
      </div>

      <div className="skeleton-panel">
        <div className="skeleton-table">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton-list-row">
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 2 }}>
                <SkeletonAvatar size="md" />
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', flex: 1 }}>
                  <Skeleton width="50%" height="1rem" radius="sm" />
                  <Skeleton width="35%" height="0.8rem" radius="sm" />
                </div>
              </div>
              <Skeleton width="20%" height="1rem" radius="sm" />
              <Skeleton width="15%" height="1.5rem" radius="full" />
              <Skeleton width="4rem" height="2rem" radius="md" />
            </div>
          ))}
        </div>
      </div>
    </SkeletonWrapper>
  )
}

export function PatientDetailSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie karty pacjenta…" className="skeleton-dashboard">
      <div className="skeleton-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <SkeletonAvatar size="lg" />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
            <Skeleton width="40%" height="1.75rem" radius="md" />
            <Skeleton width="25%" height="1rem" radius="sm" />
          </div>
          <Skeleton width="6rem" height="2.25rem" radius="md" />
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          gap: '0.5rem',
          borderBottom: '1px solid var(--color-border)',
          paddingBottom: '0.5rem',
        }}
      >
        <Skeleton width="6rem" height="2rem" radius="sm" />
        <Skeleton width="6rem" height="2rem" radius="sm" />
        <Skeleton width="6rem" height="2rem" radius="sm" />
      </div>

      <div className="skeleton-panel">
        <Skeleton width="30%" height="1.25rem" radius="sm" />
        <SkeletonText lines={5} gap="0.75rem" />
      </div>
    </SkeletonWrapper>
  )
}

export function ScheduleSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie harmonogramu…" className="skeleton-dashboard">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Skeleton width="35%" height="2rem" radius="md" />
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Skeleton width="6rem" height="2.25rem" radius="md" />
          <Skeleton width="8rem" height="2.25rem" radius="md" />
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', overflow: 'hidden' }}>
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} width="14%" height="4rem" radius="md" />
        ))}
      </div>

      <div className="skeleton-panel">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="skeleton-list-row">
            <Skeleton width="4rem" height="1.25rem" radius="sm" />
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '0.35rem',
                flex: 1,
                paddingLeft: '1rem',
              }}
            >
              <Skeleton width="40%" height="1rem" radius="sm" />
              <Skeleton width="25%" height="0.8rem" radius="sm" />
            </div>
            <Skeleton width="5rem" height="1.5rem" radius="full" />
          </div>
        ))}
      </div>
    </SkeletonWrapper>
  )
}

export function ExercisesSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie katalogu ćwiczeń…" className="skeleton-dashboard">
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
        <Skeleton width="50%" height="2.5rem" radius="md" />
        <Skeleton width="20%" height="2.5rem" radius="md" />
      </div>

      <div className="skeleton-card-grid">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skeleton-exercise-card">
            <Skeleton width="100%" height="140px" radius="md" />
            <Skeleton width="75%" height="1.25rem" radius="sm" />
            <Skeleton width="45%" height="0.875rem" radius="sm" />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.5rem' }}>
              <Skeleton width="40%" height="1.5rem" radius="full" />
              <Skeleton width="30%" height="1.5rem" radius="sm" />
            </div>
          </div>
        ))}
      </div>
    </SkeletonWrapper>
  )
}

export function ProfileSkeleton() {
  return (
    <SkeletonWrapper label="Ładowanie profilu…" className="skeleton-dashboard">
      <div className="skeleton-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <SkeletonAvatar size="lg" />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
            <Skeleton width="35%" height="1.75rem" radius="md" />
            <Skeleton width="20%" height="1rem" radius="sm" />
          </div>
        </div>
      </div>

      <div className="skeleton-panel">
        <Skeleton width="30%" height="1.25rem" radius="sm" />
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: '1rem',
            marginTop: '0.5rem',
          }}
        >
          <Skeleton width="100%" height="2.5rem" radius="md" />
          <Skeleton width="100%" height="2.5rem" radius="md" />
          <Skeleton width="100%" height="2.5rem" radius="md" />
          <Skeleton width="100%" height="2.5rem" radius="md" />
        </div>
      </div>
    </SkeletonWrapper>
  )
}
