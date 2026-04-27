import React, { useMemo } from 'react';
import { PortfolioSnapshot } from '@/lib/api';
import styles from './PerformanceCalendar.module.css';

interface PerformanceCalendarProps {
  snapshots: PortfolioSnapshot[];
}

const MONTHS_TR = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara'];

function cellColor(pnl: number | null): string {
  if (pnl === null) return 'rgba(100,116,139,0.08)';
  if (pnl === 0) return 'rgba(100,116,139,0.2)';
  const intensity = Math.min(Math.abs(pnl) / 3, 1); // 3% = full intensity
  const alpha = 0.4 + intensity * 0.6;
  return pnl > 0
    ? `rgba(34,197,94,${alpha.toFixed(2)})`
    : `rgba(239,68,68,${alpha.toFixed(2)})`;
}

export default function PerformanceCalendar({ snapshots }: PerformanceCalendarProps) {
  const { weeks, monthLabels } = useMemo(() => {
    const today = new Date();
    // Go back 12 months roughly
    const start = new Date(today.getFullYear(), today.getMonth() - 11, 1);
    
    // Build map for easy lookup
    const snapshotMap = new Map<string, number | null>();
    snapshots.forEach((s) => {
      snapshotMap.set(s.date, s.daily_pnl_pct);
    });

    const weeksArray: { date: Date; pnl: number | null }[][] = [];
    const monthLabelsMap = new Map<number, number>(); // weekIndex -> month string index

    // start from a Monday
    const current = new Date(start);
    const day = current.getDay();
    const diff = current.getDate() - day + (day === 0 ? -6 : 1);
    current.setDate(diff);

    let weekIndex = 0;
    let currentWeek: { date: Date; pnl: number | null }[] = [];

    while (current <= today) {
      if (current.getDate() === 1) {
        monthLabelsMap.set(weekIndex, current.getMonth());
      }
      
      const dateStr = current.toISOString().split('T')[0];
      const pnl = snapshotMap.has(dateStr) ? snapshotMap.get(dateStr) || null : null;

      currentWeek.push({ date: new Date(current), pnl });

      if (currentWeek.length === 7) {
        weeksArray.push(currentWeek);
        currentWeek = [];
        weekIndex++;
      }
      
      current.setDate(current.getDate() + 1);
    }
    
    // push last partial week if any
    if (currentWeek.length > 0) {
      // fill the rest of the week
      while (currentWeek.length < 7) {
        currentWeek.push({ date: new Date(current), pnl: null });
        current.setDate(current.getDate() + 1);
      }
      weeksArray.push(currentWeek);
    }

    return { weeks: weeksArray, monthLabels: monthLabelsMap };
  }, [snapshots]);

  return (
    <div className={`card ${styles.card}`}>
      <div className={styles.content}>
        <div className={styles.monthRow}>
          <div className={styles.daySpacer} />
          {weeks.map((_, i) => (
            <div key={`month-${i}`} className={styles.monthLabel}>
              {monthLabels.has(i) ? MONTHS_TR[monthLabels.get(i)!] : ''}
            </div>
          ))}
        </div>
        
        <div className={styles.grid}>
          <div className={styles.dayLabels}>
            <span>Pt</span>
            <span>Ça</span>
            <span>Cu</span>
          </div>
          
          <div className={styles.weeks}>
            {weeks.map((week, wIndex) => (
              <div key={wIndex} className={styles.week}>
                {week.map((day, dIndex) => (
                  <div
                    key={`${wIndex}-${dIndex}`}
                    title={`${day.date.toISOString().split('T')[0]}: ${day.pnl !== null ? (day.pnl > 0 ? '+' : '') + day.pnl.toFixed(2) + '%' : 'Veri yok'}`}
                    className={styles.cell}
                    style={{ backgroundColor: cellColor(day.pnl) }}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
        
        <div className={styles.legend}>
          <span>Piyasa Kapalı</span>
          <div className={styles.legendSwatch} style={{ backgroundColor: 'rgba(100,116,139,0.08)' }} />
          <span className={styles.legendGap}>Kayıplı</span>
          <div className={styles.legendSwatch} style={{ backgroundColor: 'rgba(239,68,68,0.7)' }} />
          <span className={styles.legendGap}>Kazançlı</span>
          <div className={styles.legendSwatch} style={{ backgroundColor: 'rgba(34,197,94,0.7)' }} />
        </div>
      </div>
    </div>
  );
}
