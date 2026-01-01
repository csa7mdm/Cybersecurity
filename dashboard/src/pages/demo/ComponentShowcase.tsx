import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Button,
    Input,
    Card,
    CardHeader,
    CardTitle,
    CardDescription,
    CardContent,
    CardFooter,
    Badge,
    Modal,
    Spinner,
} from '../../components/ui';
import {
    Shield,
    Mail,
    Search,
    Plus,
    Trash2,
    Check,
    AlertCircle,
    Lock,
} from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';

const ComponentShowcase: React.FC = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const handleDemoAction = (action: string) => {
        toast.success(`${action} clicked!`);
    };

    const simulateLoading = () => {
        setIsLoading(true);
        setTimeout(() => {
            setIsLoading(false);
            toast.success('Loading complete!');
        }, 2000);
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            <Toaster position="top-right" />

            {/* Header */}
            <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="h-10 w-10 bg-primary-600 rounded-lg flex items-center justify-center">
                                <Shield className="h-6 w-6 text-white" />
                            </div>
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                                    Component Showcase
                                </h1>
                                <p className="text-sm text-gray-600 dark:text-gray-400">
                                    Interactive demo of all UI components
                                </p>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <Link to="/onboarding">
                                <Button variant="ghost" size="sm">Onboarding Demo</Button>
                            </Link>
                            <Link to="/login">
                                <Button variant="outline" size="sm">Login</Button>
                            </Link>
                            <Link to="/signup">
                                <Button variant="primary" size="sm">Sign Up</Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                    {/* Buttons Section */}
                    <Card variant="outlined">
                        <CardHeader>
                            <CardTitle>Buttons</CardTitle>
                            <CardDescription>5 variants, 3 sizes, loading states</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Variants:</p>
                                <div className="flex flex-wrap gap-2">
                                    <Button variant="primary" onClick={() => handleDemoAction('Primary')}>
                                        Primary
                                    </Button>
                                    <Button variant="secondary" onClick={() => handleDemoAction('Secondary')}>
                                        Secondary
                                    </Button>
                                    <Button variant="outline" onClick={() => handleDemoAction('Outline')}>
                                        Outline
                                    </Button>
                                    <Button variant="ghost" onClick={() => handleDemoAction('Ghost')}>
                                        Ghost
                                    </Button>
                                    <Button variant="danger" onClick={() => handleDemoAction('Danger')}>
                                        Danger
                                    </Button>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Sizes:</p>
                                <div className="flex items-center gap-2">
                                    <Button size="sm">Small</Button>
                                    <Button size="md">Medium</Button>
                                    <Button size="lg">Large</Button>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">With Icons & Loading:</p>
                                <div className="flex flex-wrap gap-2">
                                    <Button icon={<Plus className="h-4 w-4" />}>
                                        New Scan
                                    </Button>
                                    <Button isLoading onClick={simulateLoading}>
                                        Loading
                                    </Button>
                                    <Button variant="danger" icon={<Trash2 className="h-4 w-4" />}>
                                        Delete
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Inputs Section */}
                    <Card variant="outlined">
                        <CardHeader>
                            <CardTitle>Inputs</CardTitle>
                            <CardDescription>Form inputs with validation states</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Input
                                label="Email Address"
                                type="email"
                                placeholder="you@example.com"
                                icon={<Mail className="h-4 w-4" />}
                            />

                            <Input
                                label="Password"
                                type="password"
                                placeholder="••••••••"
                                icon={<Lock className="h-4 w-4" />}
                                helperText="Must be at least 8 characters"
                            />

                            <Input
                                label="Search"
                                type="text"
                                placeholder="Search vulnerabilities..."
                                icon={<Search className="h-4 w-4" />}
                            />

                            <Input
                                label="With Error"
                                type="text"
                                error="This field is required"
                                icon={<AlertCircle className="h-4 w-4" />}
                            />
                        </CardContent>
                    </Card>

                    {/* Badges Section */}
                    <Card variant="outlined">
                        <CardHeader>
                            <CardTitle>Badges</CardTitle>
                            <CardDescription>Severity indicators and status tags</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Severity Levels:</p>
                                <div className="flex flex-wrap gap-2">
                                    <Badge variant="critical" dot>2 Critical</Badge>
                                    <Badge variant="high" dot>5 High</Badge>
                                    <Badge variant="medium" dot>8 Medium</Badge>
                                    <Badge variant="low" dot>12 Low</Badge>
                                    <Badge variant="info" dot>15 Info</Badge>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Other Variants:</p>
                                <div className="flex flex-wrap gap-2">
                                    <Badge variant="success">Active</Badge>
                                    <Badge variant="warning">Pending</Badge>
                                    <Badge variant="default">Completed</Badge>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Sizes:</p>
                                <div className="flex items-center gap-2">
                                    <Badge size="sm">Small</Badge>
                                    <Badge size="md">Medium</Badge>
                                    <Badge size="lg">Large</Badge>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Cards Section */}
                    <Card variant="outlined">
                        <CardHeader>
                            <CardTitle>Cards</CardTitle>
                            <CardDescription>Container components with variants</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Card variant="default" padding="sm">
                                <CardTitle className="text-base">Default Card</CardTitle>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    Basic card with small padding
                                </p>
                            </Card>

                            <Card variant="outlined" padding="md">
                                <CardTitle className="text-base">Outlined Card</CardTitle>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    Card with border and medium padding
                                </p>
                            </Card>

                            <Card variant="elevated" padding="sm">
                                <CardTitle className="text-base">Elevated Card</CardTitle>
                                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    Card with shadow elevation
                                </p>
                            </Card>
                        </CardContent>
                    </Card>

                    {/* Modal & Spinner Section */}
                    <Card variant="outlined">
                        <CardHeader>
                            <CardTitle>Modal & Spinner</CardTitle>
                            <CardDescription>Dialogs and loading indicators</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Modal:</p>
                                <Button onClick={() => setIsModalOpen(true)}>
                                    Open Modal
                                </Button>
                            </div>

                            <div className="space-y-2">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Spinners:</p>
                                <div className="flex items-center gap-4">
                                    <Spinner size="sm" />
                                    <Spinner size="md" />
                                    <Spinner size="lg" />
                                    <Spinner size="xl" variant="primary" />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Loading Demo:</p>
                                <Button onClick={simulateLoading} isLoading={isLoading}>
                                    {isLoading ? 'Loading...' : 'Start Loading'}
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Example Scan Card */}
                    <Card variant="elevated" className="lg:col-span-2">
                        <CardHeader>
                            <div className="flex items-center justify-between">
                                <div>
                                    <CardTitle>Recent Scan Results</CardTitle>
                                    <CardDescription>Example of components in action</CardDescription>
                                </div>
                                <Badge variant="success" dot>Completed</Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="grid grid-cols-4 gap-4">
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">2</div>
                                        <div className="text-sm text-gray-600 dark:text-gray-400">Critical</div>
                                        <Badge variant="critical" size="sm" className="mt-1">High Priority</Badge>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">5</div>
                                        <div className="text-sm text-gray-600 dark:text-gray-400">High</div>
                                        <Badge variant="high" size="sm" className="mt-1">Review Now</Badge>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">8</div>
                                        <div className="text-sm text-gray-600 dark:text-gray-400">Medium</div>
                                        <Badge variant="medium" size="sm" className="mt-1">Monitor</Badge>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">12</div>
                                        <div className="text-sm text-gray-600 dark:text-gray-400">Low</div>
                                        <Badge variant="low" size="sm" className="mt-1">Informational</Badge>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                        <CardFooter className="gap-2">
                            <Button variant="primary" icon={<Check className="h-4 w-4" />}>
                                Generate Report
                            </Button>
                            <Button variant="outline">
                                View Details
                            </Button>
                        </CardFooter>
                    </Card>
                </div>
            </div>

            {/* Demo Modal */}
            <Modal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                title="Demo Modal"
                description="This is an example modal dialog"
                size="md"
            >
                <div className="space-y-4">
                    <p className="text-gray-600 dark:text-gray-400">
                        This modal demonstrates:
                    </p>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 dark:text-gray-400">
                        <li>Backdrop with blur effect</li>
                        <li>Keyboard navigation (ESC to close)</li>
                        <li>Body scroll lock</li>
                        <li>Smooth animations</li>
                        <li>Accessibility (ARIA labels)</li>
                    </ul>
                    <div className="flex gap-2 justify-end pt-4">
                        <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                            Cancel
                        </Button>
                        <Button
                            variant="primary"
                            onClick={() => {
                                setIsModalOpen(false);
                                toast.success('Action confirmed!');
                            }}
                        >
                            Confirm
                        </Button>
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default ComponentShowcase;
