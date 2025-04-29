// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { fireEvent, render, screen } from '@testing-library/react';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { getMockedAnnotation } from '../../../../test-utils/mocked-items-factory/mocked-annotations';
import { getAllWithMatchId, getById } from '../../../../test-utils/utils';
import { AnnotationSceneProvider, useAnnotationScene } from './annotation-scene-provider.component';

describe('Annotation scene provider - annotation list actions', (): void => {
    let annotations: Annotation[] = [];

    beforeEach(() => {
        annotations = [
            getMockedAnnotation({ id: 'rect-1' }, ShapeType.Rect),
            getMockedAnnotation({ id: 'rect-2', isSelected: true, isHidden: true, isLocked: true }, ShapeType.Rect),
            getMockedAnnotation({ id: 'rect-3', isSelected: true, isLocked: true }, ShapeType.Rect),
        ];
    });

    const AnnotationList = () => {
        const scene = useAnnotationScene();

        return (
            <div title='annotations'>
                {scene.annotations.map((annotation) => (
                    <ul key={annotation.id}>
                        <li id={`${annotation.id}-selected-${annotation.isSelected}`}></li>
                        <li id={`${annotation.id}-hidden-${annotation.isHidden}`}></li>
                        <li id={`${annotation.id}-locked-${annotation.isLocked}`}></li>
                    </ul>
                ))}
            </div>
        );
    };

    const HideAllApp = (): JSX.Element => {
        const scene = useAnnotationScene();
        const hideAllHandler = () => {
            scene.setHiddenAnnotations((_annotation) => true);
        };

        return (
            <>
                <button onClick={hideAllHandler}>Hide all</button>
            </>
        );
    };

    const SelectAllApp = ({ isSelected = false }: { isSelected?: boolean }): JSX.Element => {
        const scene = useAnnotationScene();
        const selectUnselectHandler = () => {
            scene.setSelectedAnnotations((_annotation) => isSelected);
        };

        return (
            <>
                <button id='select-unselect-button' onClick={selectUnselectHandler}>
                    Select all
                </button>
            </>
        );
    };

    const ToggleLockSelected = ({ isLocked }: { isLocked: boolean }): JSX.Element => {
        const scene = useAnnotationScene();
        const toggleLockHandler = () => {
            scene.setLockedAnnotations((annotation) => (annotation.isSelected ? isLocked : annotation.isLocked));
        };

        return (
            <>
                <button id='toggle-lock-button' onClick={toggleLockHandler}>
                    Toggle lock
                </button>
            </>
        );
    };

    const SelectAnnotation = ({ annotationId }: { annotationId: string }): JSX.Element => {
        const scene = useAnnotationScene();
        const unselectHandler = () => {
            scene.unselectAnnotation(annotationId);
        };

        const selectHandler = () => {
            scene.selectAnnotation(annotationId);
        };

        return (
            <>
                <button id='unselect-button' onClick={unselectHandler}>
                    Unselect
                </button>

                <button id='select-button' onClick={selectHandler}>
                    Select
                </button>
            </>
        );
    };

    const ToggleVisibility = ({
        isHidden,
        fromSelected = false,
        annotationId = undefined,
    }: {
        isHidden: boolean;
        fromSelected?: boolean;
        annotationId?: string;
    }): JSX.Element => {
        const scene = useAnnotationScene();

        const toggleVisibilityHandler = () => {
            scene.setHiddenAnnotations((annotation) => (annotation.isSelected ? isHidden : annotation.isHidden));
        };

        const showHandler = () => {
            annotationId && scene.showAnnotation(annotationId);
        };

        const hideHandler = () => {
            annotationId && scene.hideAnnotation(annotationId);
        };

        return (
            <>
                {fromSelected ? (
                    <button id='toggle-visibility-button' onClick={toggleVisibilityHandler}>
                        Toggle visibility
                    </button>
                ) : isHidden ? (
                    <button id='hide-button' onClick={hideHandler} />
                ) : (
                    <button id='show-button' onClick={showHandler} />
                )}
            </>
        );
    };

    const ToggleLockApp = ({ annotationId = '' }: { annotationId?: string }): JSX.Element => {
        const scene = useAnnotationScene();

        const toggleLock = () => {
            scene.toggleLock(true, annotationId);
        };

        return (
            <>
                <button id='toggle-lock-button' onClick={toggleLock}>
                    Toggle lock
                </button>
            </>
        );
    };

    it('selectAll(true) function', (): void => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <SelectAllApp isSelected />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        const button = getById(container, 'select-unselect-button');
        button && fireEvent.click(button);
        const selected = getAllWithMatchId(container, '-selected-true');
        expect(selected).toHaveLength(annotations.length);
    });

    it('selectAll(false) function', (): void => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <SelectAllApp />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        const button = getById(container, 'select-unselect-button');
        button && fireEvent.click(button);
        const selected = getAllWithMatchId(container, '-selected-true');
        expect(selected).toHaveLength(0);
    });

    it('toggleLock(true) on first annotation', () => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <ToggleLockApp annotationId={'rect-1'} />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        const button = getById(container, 'toggle-lock-button');
        button && fireEvent.click(button);

        const locked = getById(container, 'rect-1-locked-true');
        expect(locked).toBeInTheDocument();
    });

    it('toggleLockSelectedAnnotations - second and third should be locked', () => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <ToggleLockSelected isLocked={true} />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        const button = getById(container, 'toggle-lock-button');
        button && fireEvent.click(button);

        const locked = getAllWithMatchId(container, '-locked-true');
        expect(locked).toHaveLength(2);
    });

    it('toggleVisibilitySelectedAnnotations - second and third should be hidden', () => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <ToggleVisibility isHidden={true} fromSelected={true} />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        const button = getById(container, 'toggle-visibility-button');
        button && fireEvent.click(button);

        const locked = getAllWithMatchId(container, '-hidden-true');
        expect(locked).toHaveLength(2);
    });

    it('toggleVisibility - react-1 should be hidden', () => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <ToggleVisibility isHidden={true} annotationId={'rect-1'} />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        const visibleRect1 = getById(container, 'rect-1-hidden-false');
        expect(visibleRect1).toBeInTheDocument();

        const button = getById(container, 'hide-button');
        expect(button).toBeInTheDocument();
        button && fireEvent.click(button);

        const hiddenRect1 = getById(container, 'rect-1-hidden-true');
        expect(hiddenRect1).toBeInTheDocument();
    });

    it('toggleVisibility - react-2 should be visible', () => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <ToggleVisibility isHidden={false} annotationId={'rect-2'} />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        const visibleRect2 = getById(container, 'rect-2-hidden-true');
        expect(visibleRect2).toBeInTheDocument();

        const button = getById(container, 'show-button');
        expect(button).toBeInTheDocument();
        button && fireEvent.click(button);

        const hiddenRect2 = getById(container, 'rect-2-hidden-false');
        expect(hiddenRect2).toBeInTheDocument();
    });

    it('unselectAnnotation rect-2 should be unselect', () => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <SelectAnnotation annotationId={'rect-2'} />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        const selectRect2 = getById(container, 'rect-2-selected-true');
        expect(selectRect2).toBeInTheDocument();

        const button = getById(container, 'unselect-button');
        button && fireEvent.click(button);

        const unselectRect2 = getById(container, 'rect-2-selected-false');
        expect(unselectRect2).toBeInTheDocument();
    });

    it('selectAnnotation rect-1 should be selected', () => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <SelectAnnotation annotationId={'rect-1'} />
                <AnnotationList />
            </AnnotationSceneProvider>
        );
        const unselectRect1 = getById(container, 'rect-1-selected-false');
        expect(unselectRect1).toBeInTheDocument();

        const button = getById(container, 'select-button');
        button && fireEvent.click(button);

        const selectRect1 = getById(container, 'rect-1-selected-true');
        expect(selectRect1).toBeInTheDocument();
    });

    it('hide all Annotations', () => {
        const { container } = render(
            <AnnotationSceneProvider annotations={annotations} labels={[]}>
                <HideAllApp />
                <AnnotationList />
            </AnnotationSceneProvider>
        );

        const button = screen.getByRole('button', { name: 'Hide all' });
        fireEvent.click(button);
        annotations.forEach((annotation: Annotation) => {
            expect(getById(container, `${annotation.id}-hidden-true`)).toBeInTheDocument();
        });
    });
});
