<?php

/**
 * This is the model class for table "question_translation".
 *
 * The followings are the available columns in table 'question_translation':
 * @property integer $id
 * @property integer $question_id
 * @property integer $language_id
 * @property string $title
 * @property string $text
 * @property string $data
 *
 * The followings are the available model relations:
 * @property Language $language
 * @property Question $question
 */
class QuestionTranslation extends CActiveRecord {

    /**
     * Returns the static model of the specified AR class.
     * @param string $className active record class name.
     * @return QuestionTranslation the static model class
     */
    public static function model($className = __CLASS__) {
        return parent::model($className);
    }

    /**
     * @return string the associated database table name
     */
    public function tableName() {
        return 'question_translation';
    }

    /**
     * @return array validation rules for model attributes.
     */
    public function rules() {
        // NOTE: you should only define rules for those attributes that
        // will receive user inputs.
        return array(
            array('question_id, language_id, title', 'required'),
            array('question_id, language_id', 'numerical', 'integerOnly' => true),
            array('title', 'length', 'max' => 255),
            array('text, data', 'safe'),
            // The following rule is used by search().
            // Please remove those attributes that should not be searched.
            array('id, question_id, language_id, title, text, data', 'safe', 'on' => 'search'),
        );
    }

    /**
     * @return array relational rules.
     */
    public function relations() {
        // NOTE: you may need to adjust the relation name and the related
        // class name for the relations automatically generated below.
        return array(
            'language' => array(self::BELONGS_TO, 'Language', 'language_id'),
            'question' => array(self::BELONGS_TO, 'Question', 'question_id'),
        );
    }

    /**
     * @return array customized attribute labels (name=>label)
     */
    public function attributeLabels() {
        return array(
            'id' => Yii::t('app', 'id'),
            'question_id' => Yii::t('app', 'question_id'),
            'language_id' => Yii::t('app', 'language_id'),
            'title' => Yii::t('app', 'title'),
            'text' => Yii::t('app', 'text'),
            'data' => Yii::t('app', 'data'),
        );
    }

    public function getCanView() {
        return $this->CanView();
    }

    public function CanView() {
        return true;
    }

    public function getCanUpdate() {
        return $this->CanUpdate();
    }

    public function CanUpdate() {
        return true;
    }

    public function getCanDelete() {
        return $this->CanDelete();
    }

    public function CanDelete() {
        return true;
    }

    /**
     * Retrieves a list of models based on the current search/filter conditions.
     * @return CActiveDataProvider the data provider that can return the models based on the search/filter conditions.
     */
    public function search($show_all = false) {
        // Warning: Please modify the following code to remove attributes that
        // should not be searched.

        $criteria = new CDbCriteria;

        $criteria->compare('id', $this->id);
        $criteria->compare('question_id', $this->question_id);
        $criteria->compare('language_id', $this->language_id);
        $criteria->compare('title', $this->title, true);
        $criteria->compare('text', $this->text, true);
        $criteria->compare('data', $this->data, true);

        $pagination = true;
        if ($show_all) {
            $pagination = false;
        }

        $options =  array(
            'criteria' => $criteria,
        );
        
        if($pagination == false){
            $options['pagination'] = false;
        }
        
        return new CActiveDataProvider($this,$options);
    }

}