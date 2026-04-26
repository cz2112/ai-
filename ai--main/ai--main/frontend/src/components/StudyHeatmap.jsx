import { useMemo } from 'react';

const LEVELS = [
  'bg-gray-100 dark:bg-gray-800',
  'bg-green-200 dark:bg-green-900',
  'bg-green-400 dark:bg-green-700',
  'bg-green-600 dark:bg-green-500',
];

export default function StudyHeatmap({ data = [] }) {
  const { grid, months } = useMemo(() => {
    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(startDate.getDate() - 364); // 52 weeks

    const dataMap = {};
    data.forEach((d) => { dataMap[d.date] = d.count; });

    const weeks = [];
    const monthLabels = [];
    let currentDate = new Date(startDate);
    let lastMonth = -1;

    while (currentDate <= today) {
      const weekIndex = Math.floor((currentDate - startDate) / (7 * 24 * 60 * 60 * 1000));
      const dayOfWeek = currentDate.getDay();
      const dateStr = currentDate.toISOString().split('T')[0];
      const count = dataMap[dateStr] || 0;

      if (!weeks[weekIndex]) weeks[weekIndex] = [];
      weeks[weekIndex][dayOfWeek] = { date: dateStr, count };

      const month = currentDate.getMonth();
      if (month !== lastMonth) {
        monthLabels.push({ label: currentDate.toLocaleString('default', { month: 'short' }), weekIndex });
        lastMonth = month;
      }

      currentDate.setDate(currentDate.getDate() + 1);
    }

    return { grid: weeks, months: monthLabels };
  }, [data]);

  const getLevel = (count) => {
    if (count === 0) return 0;
    if (count <= 2) return 1;
    if (count <= 5) return 2;
    return 3;
  };

  return (
    <div>
      <div className="flex gap-1 text-xs text-gray-400 dark:text-gray-500 mb-1 ml-8">
        {months.map((m, i) => (
          <span key={i} style={{ marginLeft: `${Math.max(0, (m.weekIndex - (i > 0 ? months[i - 1].weekIndex : 0) - 1)) * 14}px` }}>
            {m.label}
          </span>
        ))}
      </div>
      <div className="flex gap-[3px] overflow-x-auto">
        <div className="flex flex-col gap-[3px] text-xs text-gray-400 dark:text-gray-500 mr-1">
          <span className="h-[12px]"></span>
          <span className="h-[12px] leading-[12px]">Mon</span>
          <span className="h-[12px]"></span>
          <span className="h-[12px] leading-[12px]">Wed</span>
          <span className="h-[12px]"></span>
          <span className="h-[12px] leading-[12px]">Fri</span>
          <span className="h-[12px]"></span>
        </div>
        {grid.map((week, wi) => (
          <div key={wi} className="flex flex-col gap-[3px]">
            {[0, 1, 2, 3, 4, 5, 6].map((day) => {
              const cell = week?.[day];
              if (!cell) return <div key={day} className="w-[12px] h-[12px]" />;
              const level = getLevel(cell.count);
              return (
                <div
                  key={day}
                  className={`w-[12px] h-[12px] rounded-sm ${LEVELS[level]}`}
                  title={`${cell.date}: ${cell.count} activities`}
                />
              );
            })}
          </div>
        ))}
      </div>
      <div className="flex items-center gap-1 mt-2 text-xs text-gray-400 dark:text-gray-500">
        <span>Less</span>
        {LEVELS.map((cls, i) => (
          <div key={i} className={`w-[12px] h-[12px] rounded-sm ${cls}`} />
        ))}
        <span>More</span>
      </div>
    </div>
  );
}
