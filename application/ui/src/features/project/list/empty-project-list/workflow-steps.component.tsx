// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Fragment, useLayoutEffect, useRef, useState, type ComponentType, type SVGProps } from 'react';

import { Text } from '@geti-ui/ui';

import classes from './workflow-steps.module.scss';

interface WorkflowStep {
    label: string;
    icon: ComponentType<SVGProps<SVGSVGElement>>;
}

const FolderIcon = (props: SVGProps<SVGSVGElement>) => (
    <svg viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth={1.8} {...props}>
        <path d='M3.5 7.5h6l2 2h9v8.5a2 2 0 0 1-2 2h-15z' />
        <path d='M3.5 7.5v-2h5l2 2' />
    </svg>
);

const EditIcon = (props: SVGProps<SVGSVGElement>) => (
    <svg viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth={1.8} {...props}>
        <path d='M5 19h4l10-10-4-4L5 15z' />
        <path d='M13.5 6.5l4 4' />
    </svg>
);

const ModelIcon = (props: SVGProps<SVGSVGElement>) => (
    <svg viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth={1.8} {...props}>
        <path d='M12 3.5 20 8v8l-8 4.5L4 16V8z' />
        <path d='M12 12 20 8' />
        <path d='M12 12v8.5' />
        <path d='M12 12 4 8' />
    </svg>
);

const ChartIcon = (props: SVGProps<SVGSVGElement>) => (
    <svg viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth={1.8} {...props}>
        <path d='M4 19.5h16' />
        <path d='M7 16v-5' />
        <path d='M12 16V7' />
        <path d='M17 16v-8' />
    </svg>
);

const DeployIcon = (props: SVGProps<SVGSVGElement>) => (
    <svg viewBox='0 0 24 24' fill='none' stroke='currentColor' strokeWidth={1.8} {...props}>
        <path d='M12 3.5v11' />
        <path d='m8 7.5 4-4 4 4' />
        <path d='M5 14.5v4a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-4' />
    </svg>
);

const STEPS: WorkflowStep[] = [
    { label: 'Add data', icon: FolderIcon },
    { label: 'Annotate', icon: EditIcon },
    { label: 'Train', icon: ModelIcon },
    { label: 'Evaluate', icon: ChartIcon },
    { label: 'Deploy', icon: DeployIcon },
];

// The return loop runs from the centre of the last step circle back to the centre of the
// first one. Label widths vary, so the span is measured instead of being hard-coded.
const useLoopSpan = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [span, setSpan] = useState({ left: 0, width: 0 });

    useLayoutEffect(() => {
        const container = containerRef.current;

        if (container === null) {
            return;
        }

        const measure = () => {
            const circles = container.querySelectorAll<HTMLElement>('[data-step-circle]');
            const first = circles[0];
            const last = circles[circles.length - 1];

            if (first === undefined || last === undefined) {
                return;
            }

            const left = first.offsetLeft + first.offsetWidth / 2;
            const right = last.offsetLeft + last.offsetWidth / 2;

            setSpan({ left, width: right - left });
        };

        measure();

        if (typeof ResizeObserver === 'undefined') {
            return;
        }

        const observer = new ResizeObserver(measure);
        observer.observe(container);

        return () => observer.disconnect();
    }, []);

    return { containerRef, span };
};

export const WorkflowSteps = () => {
    const { containerRef, span } = useLoopSpan();

    return (
        <div ref={containerRef} className={classes.workflow}>
            <div role='list' aria-label='Geti workflow' className={classes.steps}>
                {STEPS.map(({ label, icon: Icon }, index) => (
                    <Fragment key={label}>
                        {index > 0 && <span className={classes.link} aria-hidden />}
                        <div role='listitem' className={classes.step}>
                            <span className={classes.circle} data-step-circle aria-hidden>
                                <Icon />
                            </span>
                            <Text UNSAFE_className={classes.label}>{label}</Text>
                        </div>
                    </Fragment>
                ))}
            </div>

            <div className={classes.loop} style={{ left: span.left, width: span.width }}>
                <Text UNSAFE_className={classes.loopText}>Inference collects new data — retrain and improve</Text>
            </div>
        </div>
    );
};
