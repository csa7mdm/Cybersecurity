import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Input, Card, CardContent } from '../../components/ui';
import { Check, ArrowRight, ArrowLeft, Building2, Users, Gift, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

interface OnboardingData {
    organizationName: string;
    industry: string;
    companySize: string;
    teamEmails: string[];
}

const OnboardingWizard: React.FC = () => {
    const navigate = useNavigate();
    const [currentStep, setCurrentStep] = useState(0);
    const [data, setData] = useState<OnboardingData>({
        organizationName: '',
        industry: '',
        companySize: '',
        teamEmails: [''],
    });

    const steps = [
        { title: 'Welcome', icon: Sparkles },
        { title: 'Organization', icon: Building2 },
        { title: 'Team', icon: Users },
        { title: 'Activate Trial', icon: Gift },
    ];

    const industries = [
        'Technology',
        'Finance',
        'Healthcare',
        'E-commerce',
        'Manufacturing',
        'Education',
        'Other',
    ];

    const companySizes = ['1-10', '11-50', '51-200', '201-500', '500+'];

    const handleNext = () => {
        if (currentStep < steps.length - 1) {
            setCurrentStep(currentStep + 1);
        } else {
            // Final step - activate trial
            toast.success('🎉 Trial activated! Welcome aboard!');
            setTimeout(() => navigate('/dashboard'), 1500);
        }
    };

    const handleBack = () => {
        if (currentStep > 0) {
            setCurrentStep(currentStep - 1);
        }
    };

    const updateData = (field: keyof OnboardingData, value: any) => {
        setData({ ...data, [field]: value });
    };

    const addTeamMember = () => {
        setData({ ...data, teamEmails: [...data.teamEmails, ''] });
    };

    const updateTeamEmail = (index: number, email: string) => {
        const newEmails = [...data.teamEmails];
        newEmails[index] = email;
        setData({ ...data, teamEmails: newEmails });
    };

    const removeTeamMember = (index: number) => {
        const newEmails = data.teamEmails.filter((_, i) => i !== index);
        setData({ ...data, teamEmails: newEmails });
    };

    const canProceed = () => {
        switch (currentStep) {
            case 0:
                return true; // Welcome step
            case 1:
                return data.organizationName && data.industry && data.companySize;
            case 2:
                return true; // Team step is optional
            case 3:
                return true; // Trial activation
            default:
                return false;
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
            <div className="w-full max-w-3xl">
                {/* Progress Indicator */}
                <div className="mb-8">
                    <div className="flex items-center justify-between">
                        {steps.map((step, index) => {
                            const Icon = step.icon;
                            const isActive = index === currentStep;
                            const isCompleted = index < currentStep;

                            return (
                                <React.Fragment key={index}>
                                    <div className="flex flex-col items-center">
                                        <div
                                            className={`
                        w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all
                        ${isCompleted ? 'bg-primary-600 text-white' : ''}
                        ${isActive ? 'bg-primary-600 text-white ring-4 ring-primary-100 dark:ring-primary-900' : ''}
                        ${!isActive && !isCompleted ? 'bg-gray-200 dark:bg-gray-700 text-gray-400' : ''}
                      `}
                                        >
                                            {isCompleted ? (
                                                <Check className="h-6 w-6" />
                                            ) : (
                                                <Icon className="h-6 w-6" />
                                            )}
                                        </div>
                                        <span className={`text-sm font-medium ${isActive || isCompleted ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400'}`}>
                                            {step.title}
                                        </span>
                                    </div>

                                    {index < steps.length - 1 && (
                                        <div className={`flex-1 h-0.5 mx-4 ${isCompleted ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'}`} />
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </div>
                </div>

                <Card variant="elevated">
                    <CardContent className="p-8">
                        {/* Step 0: Welcome */}
                        {currentStep === 0 && (
                            <div className="text-center space-y-6">
                                <div className="h-20 w-20 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mx-auto">
                                    <Sparkles className="h-10 w-10 text-primary-600" />
                                </div>
                                <div>
                                    <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                                        Welcome to CyperSecurity!
                                    </h2>
                                    <p className="text-lg text-gray-600 dark:text-gray-400">
                                        Let's get you set up in just a few steps
                                    </p>
                                </div>
                                <div className="grid grid-cols-3 gap-4 py-6">
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-primary-600">2 min</div>
                                        <div className="text-sm text-gray-600 dark:text-gray-400">Quick Setup</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-primary-600">14 days</div>
                                        <div className="text-sm text-gray-600 dark:text-gray-400">Free Trial</div>
                                    </div>
                                    <div className="text-center">
                                        <div className="text-2xl font-bold text-primary-600">No CC</div>
                                        <div className="text-sm text-gray-600 dark:text-gray-400">Required</div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Step 1: Organization Setup */}
                        {currentStep === 1 && (
                            <div className="space-y-6">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                                        Organization Details
                                    </h2>
                                    <p className="text-gray-600 dark:text-gray-400">
                                        Tell us about your organization
                                    </p>
                                </div>

                                <Input
                                    label="Organization Name"
                                    placeholder="Acme Corporation"
                                    value={data.organizationName}
                                    onChange={(e) => updateData('organizationName', e.target.value)}
                                    icon={<Building2 className="h-4 w-4" />}
                                />

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Industry
                                    </label>
                                    <select
                                        value={data.industry}
                                        onChange={(e) => updateData('industry', e.target.value)}
                                        className="w-full h-10 px-3 py-2 text-base border rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
                                    >
                                        <option value="">Select industry...</option>
                                        {industries.map((industry) => (
                                            <option key={industry} value={industry}>
                                                {industry}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                        Company Size
                                    </label>
                                    <div className="grid grid-cols-3 gap-2">
                                        {companySizes.map((size) => (
                                            <button
                                                key={size}
                                                type="button"
                                                onClick={() => updateData('companySize', size)}
                                                className={`
                          px-4 py-2 rounded-md text-sm font-medium transition-colors
                          ${data.companySize === size
                                                        ? 'bg-primary-600 text-white'
                                                        : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                                                    }
                        `}
                                            >
                                                {size}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Step 2: Team Invitation */}
                        {currentStep === 2 && (
                            <div className="space-y-6">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                                        Invite Your Team
                                    </h2>
                                    <p className="text-gray-600 dark:text-gray-400">
                                        Collaborate with your security team (optional)
                                    </p>
                                </div>

                                <div className="space-y-3">
                                    {data.teamEmails.map((email, index) => (
                                        <div key={index} className="flex gap-2">
                                            <Input
                                                type="email"
                                                placeholder="teammate@example.com"
                                                value={email}
                                                onChange={(e) => updateTeamEmail(index, e.target.value)}
                                            />
                                            {data.teamEmails.length > 1 && (
                                                <Button
                                                    variant="outline"
                                                    onClick={() => removeTeamMember(index)}
                                                >
                                                    Remove
                                                </Button>
                                            )}
                                        </div>
                                    ))}
                                </div>

                                <Button
                                    variant="outline"
                                    onClick={addTeamMember}
                                    icon={<Users className="h-4 w-4" />}
                                >
                                    Add Team Member
                                </Button>

                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    You can invite more team members later from the dashboard
                                </p>
                            </div>
                        )}

                        {/* Step 3: Trial Activation */}
                        {currentStep === 3 && (
                            <div className="text-center space-y-6">
                                <div className="h-20 w-20 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mx-auto">
                                    <Gift className="h-10 w-10 text-primary-600" />
                                </div>
                                <div>
                                    <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                                        Activate Your Free Trial
                                    </h2>
                                    <p className="text-lg text-gray-600 dark:text-gray-400">
                                        Get full access to Pro features for 14 days
                                    </p>
                                </div>

                                <div className="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-6 space-y-3">
                                    <div className="flex items-center justify-center gap-2 text-primary-700 dark:text-primary-300">
                                        <Check className="h-5 w-5" />
                                        <span>1,000 scans per month</span>
                                    </div>
                                    <div className="flex items-center justify-center gap-2 text-primary-700 dark:text-primary-300">
                                        <Check className="h-5 w-5" />
                                        <span>Advanced PDF reports</span>
                                    </div>
                                    <div className="flex items-center justify-center gap-2 text-primary-700 dark:text-primary-300">
                                        <Check className="h-5 w-5" />
                                        <span>All integrations (Slack, PagerDuty)</span>
                                    </div>
                                    <div className="flex items-center justify-center gap-2 text-primary-700 dark:text-primary-300">
                                        <Check className="h-5 w-5" />
                                        <span>Priority support</span>
                                    </div>
                                </div>

                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                    No credit card required • Cancel anytime
                                </p>
                            </div>
                        )}

                        {/* Navigation Buttons */}
                        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                            <Button
                                variant="outline"
                                onClick={handleBack}
                                disabled={currentStep === 0}
                                icon={<ArrowLeft className="h-4 w-4" />}
                            >
                                Back
                            </Button>

                            <Button
                                variant="primary"
                                onClick={handleNext}
                                disabled={!canProceed()}
                                icon={currentStep === steps.length - 1 ? <Check className="h-4 w-4" /> : <ArrowRight className="h-4 w-4" />}
                            >
                                {currentStep === steps.length - 1 ? 'Activate Trial' : 'Continue'}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default OnboardingWizard;
