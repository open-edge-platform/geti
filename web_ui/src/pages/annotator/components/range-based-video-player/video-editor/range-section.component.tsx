// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MouseEventHandler, MutableRefObject, useRef, useState } from 'react';

import { Overlay } from '@react-spectrum/overlays';

import { LabeledVideoRange } from '../../../../../core/annotations/labeled-video-range.interface';
import { Label } from '../../../../../core/labels/label.interface';
import { isAnomalous } from '../../../../../core/labels/utils';
import { hasEqualId } from '../../../../../shared/utils';
import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { LabelSearch } from '../../labels/label-search/label-search.component';
import { SelectionIndicator } from '../../labels/label-search/selection-indicator.component';

import classes from './video-player.module.scss';

const getAriaLabel = (range?: LabeledVideoRange) => {
    if (range === undefined) {
        return 'Add range';
    }

    return `Click to change label from ${range.start} to ${range.end}`;
};

const getId = (range?: LabeledVideoRange) => {
    if (range === undefined) {
        return 'range-section-id';
    }

    return `range-${range.start}-${range.end}-${idMatchingFormat(range.labels[0]?.name ?? 'empty')}-range-section-id`;
};

interface RangeSectionProps {
    leftPercentage: number;
    rightPercentage: number;
    labels: Label[];
    onSelectLabelForRange: (label: Label, range?: LabeledVideoRange) => void;
    range?: LabeledVideoRange;
    isDisabled?: boolean;
}

const OFFSET_BETWEEN_LABELS_SEARCH_AND_RANGE = 4;
const Z_INDEX_OF_LABELS_SEARCH_TO_BE_ON_TOP_OF_DIALOG = 999999;

export const RangeSection = ({
    leftPercentage,
    rightPercentage,
    labels,
    onSelectLabelForRange,
    range,
    isDisabled,
}: RangeSectionProps) => {
    const overlayRef = useRef(null);
    const triggerRef = useRef<HTMLDivElement>(null);
    // Note: We don't use useSize hook because when there are more labels, then we have scrollbar. Thus, useSize hook
    // does not return the latest size of the element.
    const [size, setSize] = useState<DOMRect | null>(null);
    const [isOpen, setIsOpen] = useState(false);

    const shouldShowLabelSuffix = !labels.some(isAnomalous);

    const shouldHaveLabelColor = range !== undefined && range.labels.length > 0;
    const shouldShowBorderRange = !shouldHaveLabelColor && range !== undefined;

    const color = shouldHaveLabelColor ? range.labels[0].color : '--spectrum-global-color-gray-200';

    const style = {
        background: color,
        left: `${leftPercentage * 100}%`,
        width: `${(rightPercentage - leftPercentage) * 100}%`,
        border: shouldShowBorderRange ? '1px dotted var(--rangeColor)' : undefined,
    };

    const handleSelectLabelWithoutLabelSearch = () => {
        onSelectLabelForRange(labels[0], range);
    };

    const handleOpenLabelSearch: MouseEventHandler = (e) => {
        if (isOpen || isDisabled) {
            return;
        }

        e.preventDefault();
        setSize(triggerRef.current?.getBoundingClientRect() ?? null);
        setIsOpen(true);
    };

    const handleAssignLabel = labels.length === 1 ? handleSelectLabelWithoutLabelSearch : handleOpenLabelSearch;

    const id = getId(range);

    return (
        <>
            <div
                className={range === undefined ? classes.createRangeSection : classes.rangeSection}
                style={style}
                aria-label={getAriaLabel(range)}
                data-testid={id}
                id={id}
                ref={triggerRef}
                onClick={handleAssignLabel}
                onContextMenu={handleAssignLabel}
            />
            {isOpen && size !== null && (
                <Overlay isOpen nodeRef={overlayRef as unknown as MutableRefObject<HTMLElement>}>
                    <div
                        style={{
                            position: 'absolute',
                            left: size.left,
                            top: size.bottom + OFFSET_BETWEEN_LABELS_SEARCH_AND_RANGE,
                            zIndex: Z_INDEX_OF_LABELS_SEARCH_TO_BE_ON_TOP_OF_DIALOG,
                        }}
                    >
                        <LabelSearch
                            labels={labels}
                            onClick={(label) => {
                                if (label !== null) {
                                    onSelectLabelForRange(label, range);
                                }
                                setIsOpen(false);
                            }}
                            onClose={() => setIsOpen(false)}
                            suffix={
                                shouldShowLabelSuffix
                                    ? (label, { isHovered }) => {
                                          const isSelected = Boolean(range?.labels.some(hasEqualId(label.id)));

                                          return <SelectionIndicator isHovered={isHovered} isSelected={isSelected} />;
                                      }
                                    : undefined
                            }
                        />
                    </div>
                </Overlay>
            )}
        </>
    );
};
