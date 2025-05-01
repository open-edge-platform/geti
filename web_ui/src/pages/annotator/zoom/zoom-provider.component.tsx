// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import {
    createContext,
    Dispatch,
    ReactNode,
    SetStateAction,
    useCallback,
    useContext,
    useEffect,
    useState,
} from 'react';

import { MissingProviderError } from '@shared/missing-provider-error';
import { runWhenTruthy } from '@shared/utils';
import { TransformWrapper, useTransformContext } from 'react-zoom-pan-pinch';

import { RegionOfInterest } from '../../../core/annotations/annotation.interface';
import { Rect } from '../../../core/annotations/shapes.interface';
import { usePrevious } from '../../../hooks/use-previous/use-previous.hook';
import { getCenterCoordinates } from './utils';

export type ZoomTarget = Omit<Rect, 'shapeType'> | undefined;

interface ZoomState {
    zoom: number;
    translation: {
        x: number;
        y: number;
    };
}

interface ZoomContextProps {
    zoomState: ZoomState;
    setZoomState: Dispatch<SetStateAction<ZoomState>>;

    zoomTarget: ZoomTarget;
    setZoomTarget: Dispatch<SetStateAction<ZoomTarget>>;
    getZoomStateForTarget: (target: Exclude<ZoomTarget, undefined>) => ZoomState;

    setZoomTargetOnRoi: (roi?: RegionOfInterest) => void;

    // we disable the double click to zoom out only when we are using pen
    isDblCLickDisabled: boolean;
    setIsDblClickDisabled: (disabled: boolean) => void;

    isPanning: boolean;
    isPanningDisabled: boolean;
    setIsPanningDisabled: (disabled: boolean) => void;

    screenSize: { width: number; height: number } | undefined;
    setScreenSize: Dispatch<SetStateAction<{ width: number; height: number } | undefined>>;

    setIsZoomDisabled: Dispatch<SetStateAction<boolean>>;

    minScale: number;
    maxScale: number;
}

interface ZoomProviderProps {
    children: ReactNode;
}

const defaultZoomState: ZoomState = {
    zoom: 1.0,
    translation: { x: 0, y: 0 },
};

const ZoomContext = createContext<ZoomContextProps | undefined>(undefined);

interface ResetInitialZoomProps {
    initialZoomState: ZoomState;
}

// The goal of this component is to override the initial props that are passed to the TransformWrapper component.
// TransformWrapper does not change the props when initialZoomState changes. This component fixes that behaviour.
const ResetInitialZoom = ({ initialZoomState }: ResetInitialZoomProps): JSX.Element => {
    const instance = useTransformContext();

    useEffect(() => {
        const {
            translation: { x, y },
            zoom,
        } = initialZoomState;

        instance.props = {
            ...instance.props,
            initialPositionX: x,
            initialPositionY: y,
            initialScale: zoom,
        };
    }, [initialZoomState, instance]);

    return <></>;
};

export const ZoomProvider = ({ children }: ZoomProviderProps): JSX.Element => {
    const [isZoomDisabled, setIsZoomDisabled] = useState<boolean>(false);
    const [isPanningDisabled, setIsPanningDisabled] = useState<boolean>(true);
    const [isPanning, setIsPanning] = useState<boolean>(false);
    const [isDblCLickDisabled, setIsDblClickDisabled] = useState<boolean>(false);

    // Once we set a new scale, it means the zoom bounds (min/max zoom) change
    // E.g. when we zoom into an annotation the new scale belongs to the annotation's bounding box dimensions,
    // and not the original image
    const [initialZoomState, setInitialZoomState] = useState<ZoomState>(defaultZoomState);
    const [zoomState, setZoomState] = useState<ZoomState>(defaultZoomState);

    const [zoomTarget, setZoomTarget] = useState<ZoomTarget>();
    const [screenSize, setScreenSize] = useState<{ width: number; height: number } | undefined>();

    const getZoomStateForTarget = useCallback(
        (target: Exclude<ZoomTarget, undefined>): ZoomState => {
            if (!screenSize || !target) {
                return zoomState;
            }
            const { scale, x, y } = getCenterCoordinates(screenSize, target);

            return { translation: { x, y }, zoom: scale };
        },
        [screenSize, zoomState]
    );

    // eslint-disable-next-line react-hooks/exhaustive-deps
    const setZoomTargetOnRoi = useCallback(
        runWhenTruthy((roi: RegionOfInterest): void => {
            // By setting a new target, the `setTransform` from `TransformZoom` will apply the correct zoomState

            setZoomTarget(roi);
            setInitialZoomState(getZoomStateForTarget(roi));
        }),
        [getZoomStateForTarget]
    );

    const previousZoomTarget = usePrevious(zoomTarget);
    useEffect(() => {
        if (zoomTarget === previousZoomTarget) {
            return;
        }

        if (zoomTarget !== undefined) {
            const imageZoomState = getZoomStateForTarget(zoomTarget);

            setInitialZoomState(imageZoomState);
        }
    }, [screenSize, getZoomStateForTarget, previousZoomTarget, zoomTarget]);

    // Allow the user to zoom out twice as much as the original zoom
    const minScale = Math.min(1, initialZoomState.zoom / 2);

    // Allow the user to zoom in so that they can see 25 individual pixels
    const maxScale = Math.round(Math.max(screenSize?.height ?? 1, screenSize?.width ?? 1) / 25);

    const value: ZoomContextProps = {
        zoomState,
        setZoomState,

        isPanning,
        isPanningDisabled,
        setIsPanningDisabled,

        isDblCLickDisabled,
        setIsDblClickDisabled,

        zoomTarget,
        setZoomTarget,
        getZoomStateForTarget,

        setZoomTargetOnRoi,

        screenSize,
        setScreenSize,

        setIsZoomDisabled,

        minScale,
        maxScale,
    };

    return (
        <ZoomContext.Provider value={value}>
            <TransformWrapper
                disabled={isZoomDisabled}
                panning={{
                    disabled: isPanningDisabled,
                    velocityDisabled: true,
                }}
                smooth
                // Decrease to allow more zooming out
                minScale={minScale}
                maxScale={maxScale}
                initialScale={initialZoomState.zoom}
                initialPositionX={initialZoomState.translation.x}
                initialPositionY={initialZoomState.translation.y}
                onPanningStart={() => setIsPanning(true)}
                onPanningStop={() => setIsPanning(false)}
                limitToBounds={false}
                doubleClick={{ mode: 'reset', disabled: isDblCLickDisabled }}
            >
                {children}
                <ResetInitialZoom initialZoomState={initialZoomState} />
            </TransformWrapper>
        </ZoomContext.Provider>
    );
};

export const useZoom = (): ZoomContextProps => {
    const context = useContext(ZoomContext);

    if (context === undefined) {
        throw new MissingProviderError('useZoom', 'ZoomProvider');
    }

    return context;
};
