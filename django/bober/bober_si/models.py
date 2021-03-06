from django.db import models
from bober_simple_competition.models import Profile, CompetitionQuestionSet, Competition, Attempt
from code_based_auth.models import Code
from django.db.models import Q, F, Sum
from django.utils.translation import ugettext as _
from collections import OrderedDict, defaultdict

# Create your models here.

SCHOOL_CATEGORIES = (
    ('ELEMENTARY', _('Elementary school')),
    ('HIGHSCHOOL', _('High school')),
    ('KINDERGARDEN', _('Kindergarden')),
)


class School(models.Model):
    def __unicode__(self):
        return u"{}, {}".format(self.name, self.post, self.category)

    name = models.CharField(unique=True, max_length=255)
    category = models.CharField(choices=SCHOOL_CATEGORIES, max_length=24)
    address = models.CharField(max_length=1024, blank=True, null=True)
    country_code = models.CharField(max_length = 2)
    postal_code = models.IntegerField(blank=True, null=True)
    post = models.CharField(max_length=255, blank=True, null=True)
    tax_number = models.CharField(max_length=12, blank=True, null=True)
    identifier = models.CharField(max_length=20, blank=True, null=True)
    headmaster = models.CharField(max_length=255, blank=True, null=True)
    
    def competitionquestionset_attempts(self, cqs, confirmed = True):
        if confirmed:
            attempts = Attempt.objects.filter(
                attemptconfirmation__by__schoolteachercode__school=s,
                attemptconfirmation__by__schoolteachercode__code__value=F('access_code'),
                competition_questionset = cqs).distinct()                
        else:
            school_access_codes = self.schoolteachercode_set.filter(
                    code__value__startswith=cqs.slug_str()
                ).values_list(
                    'code__value', flat=True
                ).distinct()
            attempts = Attempt.objects.filter(
                competition_questionset = cqs,
                access__code__in = school_access_codes
            )
        return attempts

    def assign_si_awards(self, awards, competition_questionsets=None, 
            revoked_by = None, commit = True):
        new_awards = []
        revoke_awards = []
        revoke_award_ids = set()
        # print bronze_award.threshold
        # print "school:", self
        l = []
        for cqs in competition_questionsets.all():
            bronze_award = cqs.award_set.get(name='bronasto')
            general_award = cqs.award_set.get(name='priznanje')
            max_score = cqs.questionset.questions.all().aggregate(
                Sum('max_score'))['max_score__sum']
            attempts = Attempt.objects.filter(
                competitionquestionset = cqs,
                attemptconfirmation__by__schoolteachercode__school = self,
                attemptconfirmation__by__schoolteachercode__code__value=F('access_code'),
                attemptconfirmation__by__schoolteachercode__competition_questionset = cqs,
            ).order_by(
                '-score'
            ).select_related(
                'competitor',
            ).prefetch_related(
                'attemptaward_set',
                'attemptaward_set__award'
            ).distinct()
            if attempts.count() < 1:
                continue
            l = attempts.values_list('score', flat=True)
            # print "    ", c.attempt.competitor, c.attempt.access_code, c.by
            bronze_threshold = min(l[(len(l) - 1) // 3], bronze_award.threshold)
            bronze_threshold = max(bronze_threshold, max_score / 2)
            for attempt in attempts:
                to_assign = set()
                if attempt.score >= bronze_threshold:
                    to_assign.add(bronze_award)
                else:
                    to_assign.add(general_award)
                competitor_name = u"{} {}".format(
                    attempt.competitor.first_name, 
                    attempt.competitor.last_name)
                aawards = attempt.attemptaward_set.all()
                serials = set(aawards.values_list('serial', flat=True))
                # aawards = aawards.filter(revoked_by = None)
                # print "  ", aawards
                # print "   ", serials
                for aaward in aawards:
                    if aaward.award in to_assign:
                        if aaward.competitor_name == competitor_name and \
                                aaward.school_name == self.name and \
                                aaward.group_name == aaward.award.group_name and \
                                aaward.revoked_by == None:
                            # print "    match", aaward, aaward.school_name.encode('utf-8')
                            to_assign.remove(aaward.award)
                        else:
                            # print "    revoke (data)",
                            # print u"        {}".format(aaward.competitor_name).encode('utf-8')
                            # print u"        {}".format(aaward.school_name).encode('utf-8')
                            
                            if aaward.revoked_by is None:
                                aaward.revoked_by = revoked_by
                                revoke_awards.append(aaward)
                                revoke_award_ids.add(aaward.id)
                    else:
                        # print "    revoke", aaward, aaward.school_name.encode('utf-8')
                        if aaward.revoked_by is None:
                            aaward.revoked_by = revoked_by
                            revoke_awards.append(aaward)
                            revoke_award_ids.add(aaward.id)
                # print to_assign
                for award in to_assign:
                    serial = "{}{:06}".format(award.serial_prefix, attempt.id)
                    new_serial = serial
                    i = 1
                    while new_serial in serials:
                        new_serial = "{}-{}".format(serial, i)
                        i += 1
                    # print "     assign", award
                    # print "       ", competitor_name.encode('utf-8')
                    # print "       ", self.name.encode('utf-8')
                    # print "       ", award.group_name.encode('utf-8')
                    # print "       ", new_serial, serials
                    new_awards.append(
                        AttemptAward(
                            award = award,
                            attempt = attempt,
                            competitor_name = competitor_name,
                            school_name = self.name,
                            group_name = award.group_name,
                            serial = new_serial,
                        ))
        if commit:
            assert revoked_by is not None
            AttemptAward.objects.filter(id__in = revoke_award_ids).update(
                revoked_by = revoked_by)
            #for award in revoke_awards:
            #    award.revoked_by = revoked_by
            #    award.save()
            AttemptAward.objects.bulk_create(new_awards)        
        return new_awards, revoke_awards


class SchoolTeacherCode(models.Model):
    def __unicode__(self):
        return u"{} {}:{}".format(self.school, self.teacher, self.code)

    school = models.ForeignKey(School)
    teacher = models.ForeignKey(Profile)
    competition_questionset = models.ForeignKey(
        CompetitionQuestionSet, null=True)
    code = models.ForeignKey(Code)
    
    def attempts(self, confirmed=True):
        a = Attempt.objects.filter(
            competition_questionset = self.competition_questionset,
            access_code = self.code.value,
        )
        if confirmed:
            a = a.filter(confirmed_by = self.teacher)
        return a.distinct()

    def assign_si_awards(self, revoked_by = None):
        if revoked_by is None:
            revoked_by = self.teacher
        cqs = CompetitionQuestionSet.objects.filter(schoolteachercode=self)
        awards = Award.objects.filter(questionset__schoolteachercode=self).distinct()
        self.school.assign_si_awards(awards, cqs, revoked_by)

    def attempt_awards(self, revoked=False):
        aawards = AttemptAward.objects.filter(
            attempt__attemptconfirmation__by = self.teacher,
            attempt__access_code = self.code.value,
            attempt__competitionquestionset = self.competition_questionset,
        )
        if not revoked:
            aawards = aawards.filter(revoked_by=None)
        return aawards

class SchoolCategoryQuestionSets(models.Model):
    def __unicode__(self):
        return u"{} {}".format(self.competition, self.school_category)

    class Meta:
        unique_together = (("competition", "school_category"))

    competition = models.ForeignKey(Competition)
    questionsets = models.ManyToManyField(CompetitionQuestionSet)
    school_category = models.CharField(choices=SCHOOL_CATEGORIES, max_length=24)


class Award(models.Model):
    def __unicode__(self):
        return u"{} {} ({})".format(self.name, self.questionset.name, self.threshold)

    competition = models.ForeignKey(Competition, null=True)
    name = models.CharField(max_length=256)
    group_name = models.CharField(max_length=256)
    questionset = models.ForeignKey(CompetitionQuestionSet)
    template = models.CharField(max_length=256)
    threshold = models.FloatField()
    serial_prefix = models.CharField(max_length=256)


class AttemptAward(models.Model):
    def __unicode__(self):
        return u"{} {} {} {} {} ({})".format(self.attempt.competitor, self.award,
            self.attempt.score, self.serial, self.note, self.id)

    award = models.ForeignKey(Award)
    attempt = models.ForeignKey(Attempt)
    note = models.CharField(max_length=1024, 
        blank=True, default='')
    competitor_name = models.TextField(blank=True)
    school_name = models.TextField(blank=True)
    group_name = models.TextField(blank=True)
    revoked_by = models.ForeignKey(Profile, null=True)
    serial = models.CharField(max_length=64, blank=True, default='',
        unique=True)
    files = models.ManyToManyField('AwardFile')


class AwardFile(models.Model):
    file = models.FileField()    
    recipients = models.ManyToManyField(Profile, blank=True)


class SchoolCompetition(Competition):
    class Meta:
        proxy = True

    def questionsets_for_school_category(self, school_category):
        try:
            return SchoolCategoryQuestionSets.objects.get(
                    school_category = school_category, competition=self
                ).questionsets.all()
        except Exception, e:
            pass
        return CompetitionQuestionSet.objects.none()
            
    def school_codes_create(self, school, teacher, access_code,
            code_data = None):
        for cqs in self.questionsets_for_school_category(
                school_category = school.category):
            if code_data is not None:
                code_data['competition_questionset'] = cqs.slug_str()
            self.school_code_create(school, teacher, access_code, 
                competition_questionset = cqs, code_data = code_data)

    def school_code_create(self, school, teacher, access_code, 
            competition_questionset = None,
            code_data=None):
        code = self.competitor_code_create(
            access_code, competition_questionset = competition_questionset,
            code_data = code_data)
        teacher.created_codes.add(code)
        sc = SchoolTeacherCode(teacher=teacher, school=school, 
            code=code, competition_questionset = competition_questionset)
        sc.save()



