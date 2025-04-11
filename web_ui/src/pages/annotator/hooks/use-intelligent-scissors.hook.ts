// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { PointerEvent, useEffect, useRef } from 'react';

import { useMutation } from '@tanstack/react-query';
import { Remote } from 'comlink';
import isEmpty from 'lodash/isEmpty';
import isEqual from 'lodash/isEqual';
import throttle from 'lodash/throttle';

import { Point, Polygon } from '../../../core/annotations/shapes.interface';
import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { runWhen, runWhenTruthy } from '../../../shared/utils';
import { leftRightMouseButtonHandler } from '../../utils';
import { usePolygonState } from '../tools/polygon-tool/polygon-state-provider.component';
import { PolygonMode } from '../tools/polygon-tool/polygon-tool.enum';
import {
    IntelligentScissorsMethods,
    IntelligentScissorsWorker,
    MouseEventHandlers,
} from '../tools/polygon-tool/polygon-tool.interface';
import { SetStateWrapper } from '../tools/undo-redo/use-undo-redo-state';

export interface IntelligentScissorsProps {
    zoom: number;
    polygon: Polygon | null;
    image: ImageData;
    lassoSegment: Point[];
    worker: Remote<IntelligentScissorsWorker> | undefined;
    canPathBeClosed: (point: Point) => boolean;
    setPointerLine: SetStateWrapper<Point[]>;
    setLassoSegment: SetStateWrapper<Point[]>;
    complete: (resetMode: PolygonMode | null) => void;
    setPointFromEvent: (callback: (point: Point) => void) => (event: PointerEvent<SVGElement>) => void;
    handleIsStartingPointHovered: (point: Point) => void;
}

export const useIntelligentScissors = ({
    image,
    complete,
    lassoSegment,
    setPointerLine,
    setLassoSegment,
    canPathBeClosed,
    setPointFromEvent,
    worker,
    handleIsStartingPointHovered,
}: IntelligentScissorsProps): MouseEventHandlers => {
    const isMounted = useRef(true);
    const isLoading = useRef<boolean>(false);
    const isPointerDown = useRef<boolean>(false);
    const isFreeDrawing = useRef<boolean>(false);
    const buildMapPoint = useRef<Point | null>(null);
    const intelligentScissors = useRef<Remote<IntelligentScissorsMethods> | null>(null);

    const { addNotification } = useNotification();

    const { segments, setSegments, mode, setMode, setIsIntelligentScissorsLoaded } = usePolygonState();

    useEffect(() => {
        isMounted.current = true;

        return () => {
            isMounted.current = false;
            intelligentScissors.current?.cleanImg();
        };
    }, [worker]);

    useEffect(() => {
        if (isMounted.current && image.data && worker) {
            setIsIntelligentScissorsLoaded(false);
            loadIntelligentScissors().then(() => setIsIntelligentScissorsLoaded(true));
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [image.data, worker]);

    useEffect(() => {
        updateBuildMapAfterUndoRedo();

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mode, segments]);

    const loadIntelligentScissors = async (): Promise<void> => {
        if (worker) {
            intelligentScissors.current = await new worker.IntelligentScissors(image);
        }
    };

    const updateBuildMapAfterUndoRedo = (): void => {
        if (mode !== PolygonMode.MagneticLasso || isPointerDown.current) return;

        if (isEmpty(segments)) {
            isLoading.current = false;
            intelligentScissors.current?.cleanPoints();

            return;
        }

        const lastSegment = segments.at(-1);
        const lastPoint = Array.isArray(lastSegment) ? lastSegment.at(-1) : undefined;
        const currentBuildMapPoint = buildMapPoint.current ?? { x: NaN, y: NaN };

        if (lastPoint && !isEqual(currentBuildMapPoint, lastPoint)) {
            intelligentScissors.current?.buildMap(lastPoint);
        }
    };

    const isFreeDrawingAndPathCannotBeClosed = (canBeClosed: boolean): boolean => isFreeDrawing.current && !canBeClosed;

    const onPointerDown = leftRightMouseButtonHandler(
        setPointFromEvent((point: Point): void => {
            if (isLoading.current) {
                return;
            }

            isPointerDown.current = true;

            const hasNotBuildMapOrIsDifferent = () => !buildMapPoint.current || !isEqual(buildMapPoint.current, point);

            setBuildMapAndSegment(hasNotBuildMapOrIsDifferent)(point);
        }),
        () => {
            setMode(PolygonMode.Eraser);

            isLoading.current = false;
            buildMapPoint.current = null;
            intelligentScissors.current?.cleanPoints();
        }
    );

    const onPointerMove = throttle(
        setPointFromEvent((point: Point): void => {
            if (isEmpty(segments)) return;

            if (!isPointerDown.current) {
                return mutation.mutate(point);
            }

            isFreeDrawing.current = true;
            buildMapPoint.current = null;
            isLoading.current = false;
            intelligentScissors.current?.cleanPoints();

            handleIsStartingPointHovered(point);

            setLassoSegment((newLassoSegment: Point[]) => [...newLassoSegment, point]);
            setPointerLine(() => [...segments.flat(), ...lassoSegment]);
        }),
        250
    );

    const onPointerUp = setPointFromEvent((point: Point): void => {
        const canBeClosed = canPathBeClosed(point);

        setBuildMapAndSegment(() => isFreeDrawingAndPathCannotBeClosed(canBeClosed))(point);

        if (canBeClosed) {
            complete(PolygonMode.MagneticLasso);

            isLoading.current = false;
            intelligentScissors.current?.cleanPoints();
        }

        isPointerDown.current = false;
        isFreeDrawing.current = false;
    });

    const mutation = useMutation({
        mutationFn: async (point: Point) => intelligentScissors.current?.calcPoints(point),

        onError: (): void => {
            addNotification({
                message: 'Failed to select the shape boundaries, could you please try again?',
                type: NOTIFICATION_TYPE.ERROR,
            });
        },

        onSuccess: runWhenTruthy((newPoints: Point[]) => {
            if (isMounted.current && !isEmpty(newPoints)) {
                setLassoSegment(newPoints);
                setPointerLine(() => [...segments.flat(), ...lassoSegment]);
            }
        }),

        onSettled: () => {
            isLoading.current = false;
        },
    });

    const setBuildMapAndSegment = (predicate: (point: Point) => boolean) =>
        runWhen(predicate)((point: Point) => {
            setLassoSegment([]);
            setSegments(addFirstPointOrNewOne(point));

            isLoading.current = true;
            buildMapPoint.current = point;
            intelligentScissors.current?.buildMap(point);
        });

    const addFirstPointOrNewOne = (point: Point): ((prevSegments: Point[][]) => Point[][]) | Point[][] => {
        const hasFirstPoint = !isEmpty(segments.at(-1));

        return hasFirstPoint ? (prevSegments: Point[][]) => [...prevSegments, lassoSegment] : [[point]];
    };

    return { onPointerDown, onPointerUp, onPointerMove };
};
