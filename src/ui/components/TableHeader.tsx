import React from 'react';
import { TitleRow } from './TitleRow';
import { HeaderRow } from './HeaderRow';

interface TableHeaderProps {
  startTime: Date;
  endTime: Date;
  timeRangeText: string;
  projectCount: number;
  projectWidth: number;
  timelineWidth: number;
  eventsWidth: number;
  durationWidth: number;
  activityColors: (string | ((text: string) => string))[];
}

export const TableHeader: React.FC<TableHeaderProps> = ({
  startTime,
  endTime,
  timeRangeText,
  projectCount,
  projectWidth,
  timelineWidth,
  eventsWidth,
  durationWidth,
  activityColors,
}) => {
  return (
    <>
      <TitleRow
        startTime={startTime}
        endTime={endTime}
        timeRangeText={timeRangeText}
        projectCount={projectCount}
      />
      <HeaderRow
        projectWidth={projectWidth}
        timelineWidth={timelineWidth}
        eventsWidth={eventsWidth}
        durationWidth={durationWidth}
        activityColors={activityColors}
      />
    </>
  );
};
